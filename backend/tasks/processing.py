from .base_task import BaseCeleryTask
from services.recording_result import RecordingResultService
import os
from dataclasses import asdict
import tempfile
from uuid import UUID
from models.file import FileStatus, PointCloudType
from models.recording_result import RecordingResultType
from schemas.file import FileModel
from schemas.recording_result import RecordingResultModel
from utils.files import clean_path
from utils.report_generation import (
    extract_report_sections,
    generate_pdf_report,
    translate_recording_result_type,
)
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from core.dependencies import get_database_uow, get_storage
from services.file import FileService
from services.stage import StageService


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

# use lazy imports for processing library so your main app would work without exceptions

storage = get_storage()


class ProcessingTask(BaseCeleryTask):
    abstract = True
    queue = 'processing'


@celery_app.task(
    queue='processing',
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def generate_bim_preview(bim_id: UUID) -> None:
    """
    Generate a best-effort BIM preview independently from IFC conversion.

    This intentionally is not a tracked BaseCeleryTask: preview generation is
    auxiliary and its failure must not affect the IFC -> LAZ -> Potree task.
    """
    from airbim_processing import ifc_to_image  # type: ignore

    async def run_task():
        async with get_database_uow() as uow:
            bim = await FileService.get_bim(bim_id, session=uow.session)
            if bim.preview_file_id is not None:
                return
            bim_file = bim.file

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(tmp_dir, bim_file.filename))
            storage.download_file_locally(
                bim_file.key,
                save_path=str(file_path),
            )

            image_path = ifc_to_image(
                ifc_path=str(file_path),
                output_dir=str(clean_path(tmp_dir)),
                resolution=(400, 300),
                img_format="jpg",
            )
            image_info = FileService.collect_file_data(image_path)
            storage.upload_file_locally(
                image_info["key"], str(image_path)
            )
            preview_data = FileModel(
                filename=image_info["filename"],
                key=image_info["key"],
                size=image_info["size"],
                content_type=image_info["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=bim_file.workspace_id,
            )

            async with get_database_uow() as uow:
                await FileService.save_bim_preview_file(
                    bim_id,
                    file_data=preview_data,
                    session=uow.session,
                )

    run_async(run_task())


@celery_app.task(
    base=ProcessingTask,
)
def clean_raw_scan_task(
    point_cloud_id: UUID,
    config: dict | None = None,
    *args,
    **kwargs
):
    """
    Clean/crop a stage scan LAZ in place (overwrite same storage key).

    Returns point_cloud_id for the next chain step (Potree conversion).
    """
    from airbim_processing import RawScanPipelineConfig, clean_raw_scan  # type: ignore

    async def run_task():
        async with get_database_uow() as uow:
            point_cloud = await FileService.get_point_cloud(
                point_cloud_id, session=uow.session
            )
            point_cloud_file = point_cloud.file

        pipeline_config = RawScanPipelineConfig(**(config or {}))

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(
                os.path.join(tmp_dir, point_cloud_file.filename)
            )
            storage.download_file_locally(
                point_cloud_file.key,
                save_path=str(file_path),
            )

            # overwrite locally (output_path=None)
            clean_raw_scan(
                input_path=str(file_path),
                output_path=None,
                config=pipeline_config,
            )

            async with get_database_uow() as uow:
                await FileService.overwrite_file_content(
                    point_cloud_file.id,
                    local_path=file_path,
                    storage=storage,
                    session=uow.session,
                )

        return point_cloud_id

    return run_async(run_task())


@celery_app.task(
    base=ProcessingTask,
)
def convert_bim_to_point_cloud(bim_id: UUID, task_id: UUID, *args, **kwargs) -> UUID:
    import ifcopenshell  # type: ignore
    from airbim_processing import ifc_to_laz, resolve_geo_transform  # type: ignore

    # fixed parameters for conversion
    geom_settings_params = [
        ("use-world-coords", True),
        ("convert-back-units", False),
        ("dimensionality", 1),
        ("iterator-output", 0),
        ("triangulation-type", 0),
        ("disable-opening-subtractions", False),
        ("weld-vertices", True),
        ("mesher-linear-deflection", 0.001),
        ("mesher-angular-deflection", 0.3),
        ("context-identifiers", ["Body"]),
        ("no-normals", True),
        ("generate-uvs", False),
        ("apply-default-materials", False),
        ("surface-colour", False),
        ("use-material-names", False),
        ("unify-shapes", False),
        ("reorient-shells", False),
        ("disable-boolean-result", False),
        ("boolean-attempt-2d", True),
        ("no-wire-intersection-check", False),
        ("keep-bounding-boxes", False),
        ("enable-layerset-slicing", False),
        ("no-parallel-mapping", False),
        ("cache-shapes", False)
    ]

    async def run_task():
        async with get_database_uow() as uow:

            bim = await FileService.get_bim(
                bim_id,
                session=uow.session
            )
            bim_file = bim.file

        # all in temp_dir will be deleted after its done
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(
                tmp_dir, bim_file.filename))
            output_path = clean_path(tmp_dir) / \
                f"converted_bim_{file_path.stem}.laz"

            # download bim file
            storage.download_file_locally(
                bim.file.key,
                save_path=str(file_path)
            )

            # convert
            bim_data = ifcopenshell.open(file_path)
            geo_result = resolve_geo_transform(bim_data)

            ifc_to_laz(
                ifc_file=bim_data,
                output_laz_path=str(output_path),
                global_matrix=geo_result.matrix,
                project_unit_m=geo_result.project_unit_m,
                density_points_per_m2=500,
                laz_scales=(0.001, 0.001, 0.001),
                min_points_per_element=1,
                num_threads=12,
                body_context_only=True,
                geom_settings_params=geom_settings_params,
                random_seed=42,
                visibility_filter=True,
                remove_context_objects=True
            )

            # collect file info
            file_info = FileService.collect_file_data(output_path)
            # upload result laz to the storage
            storage.upload_file_locally(file_info["key"], str(output_path))

            # collect file info
            file_data = FileModel(
                filename=file_info["filename"],
                key=file_info["key"],
                size=file_info["size"],
                content_type=file_info["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=bim_file.workspace_id
            )

            async with get_database_uow() as uow:
                point_cloud_id = await FileService.save_converted_bim_file(
                    bim.id,
                    file_data=file_data,
                    session=uow.session
                )

        return point_cloud_id
    point_cloud_id = run_async(run_task())
    return point_cloud_id


@celery_app.task(
    base=ProcessingTask
)
def compare_scan_and_plan(stage_id: UUID, tolerance: float = 0.05, *args, **kwargs) -> UUID:
    from airbim_processing import compute_deviations    # type: ignore

    async def run_task():
        async with get_database_uow() as uow:

            # get stage and its point cloud
            stage = await StageService.get_stage(stage_id, session=uow.session)
            stage_point_cloud = await FileService.get_point_cloud(
                stage.point_cloud.id, session=uow.session)
            # get bim (POINT CLOUD MUST ALREADY EXIST)
            bim = await FileService.get_bim_by_project_id(stage.project_id, session=uow.session)
            bim_point_cloud = await FileService.get_point_cloud(bim.point_cloud_id, session=uow.session)

            # get point cloud files
            # bim point cloud is the ideal point cloud
            # stage point cloud is the real point cloud (scan)
            stage_point_cloud_file = stage_point_cloud.file
            bim_point_cloud_file = bim_point_cloud.file

        with tempfile.TemporaryDirectory() as tmp_dir:
            bim_point_cloud_path = clean_path(
                os.path.join(tmp_dir, stage_point_cloud_file.filename))
            stage_point_cloud_path = clean_path(os.path.join(
                tmp_dir, bim_point_cloud_file.filename))
            output_path = clean_path(tmp_dir) / "plan_fact_result.laz"

            # download files
            storage.download_file_locally(
                bim_point_cloud_file.key,
                save_path=str(bim_point_cloud_path)
            )
            storage.download_file_locally(
                stage_point_cloud_file.key,
                save_path=str(stage_point_cloud_path)
            )

            # run comparison
            # takes time
            results = compute_deviations(
                real_laz_path=stage_point_cloud_path,
                ideal_laz_path=bim_point_cloud_path,
                output_laz_path=output_path,
                tolerance=tolerance
            )
            results = asdict(results)

            # collect file info
            file_info = FileService.collect_file_data(output_path)
            # upload result laz to the storage
            storage.upload_file_locally(file_info["key"], str(output_path))

        # save everything in the database
        async with get_database_uow() as uow:
            # result point cloud
            file_data = FileModel(
                filename=file_info["filename"],
                key=file_info["key"],
                size=file_info["size"],
                content_type=file_info["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=bim_point_cloud_file.workspace_id
            )
            result_point_cloud, _ = await FileService.create_point_cloud(
                point_cloud_type=PointCloudType.RECORDING,
                file_data=file_data,
                session=uow.session
            )
            # recording result
            # JSONB requires JSON-serializable values (dates as ISO strings)
            results["project_name"] = stage.project.name
            results["project_description"] = stage.project.description
            results["stage_name"] = stage.name
            results["stage_description"] = stage.description
            results["stage_start_date"] = (
                stage.start_date.isoformat() if stage.start_date else None
            )
            result_data = RecordingResultModel(
                project_id=stage.project_id,
                data=results,
                type=RecordingResultType.PLAN_FACT,
                point_cloud_id=result_point_cloud.id)

            recording_result = await RecordingResultService.create_recording_result(
                result_data,
                session=uow.session
            )

            return recording_result.id
    result_id = run_async(run_task())
    return result_id


@celery_app.task(
    base=ProcessingTask
)
def check_progress(
    old_stage_id: UUID,
    new_stage_id: UUID,
    tolerance: float = 0.05,
    *args,
    **kwargs
) -> UUID:
    from airbim_processing import compute_progress    # type: ignore

    async def run_task():
        async with get_database_uow() as uow:

            # get stages and their point clouds
            old_stage = await StageService.get_stage(old_stage_id, session=uow.session)
            new_stage = await StageService.get_stage(new_stage_id, session=uow.session)

            old_stage_point_cloud = await FileService.get_point_cloud(
                old_stage.point_cloud.id, session=uow.session)
            new_stage_point_cloud = await FileService.get_point_cloud(
                new_stage.point_cloud.id, session=uow.session)

            # get point cloud files
            old_point_cloud_file = old_stage_point_cloud.file
            new_point_cloud_file = new_stage_point_cloud.file

        with tempfile.TemporaryDirectory() as tmp_dir:
            # paths to existing point clouds
            old_point_cloud_path = clean_path(
                os.path.join(tmp_dir, old_point_cloud_file.filename))
            new_point_cloud_path = clean_path(
                os.path.join(tmp_dir, new_point_cloud_file.filename))

            # path to resulting point cloud
            output_path = clean_path(tmp_dir) / "progress_result.laz"

            # download files
            storage.download_file_locally(
                old_point_cloud_file.key,
                save_path=str(old_point_cloud_path)
            )
            storage.download_file_locally(
                new_point_cloud_file.key,
                save_path=str(new_point_cloud_path)
            )

            # run comparison
            # takes time
            results = compute_progress(
                before_laz_path=old_point_cloud_path,
                after_laz_path=new_point_cloud_path,
                output_laz_path=output_path,
                tolerance=tolerance
            )
            results = asdict(results)

            # collect file info
            file_info = FileService.collect_file_data(output_path)
            # upload result laz to the storage
            storage.upload_file_locally(file_info["key"], str(output_path))

        # save everything in the database
        async with get_database_uow() as uow:
            # result point cloud
            file_data = FileModel(
                filename=file_info["filename"],
                key=file_info["key"],
                size=file_info["size"],
                content_type=file_info["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=old_stage.project.workspace_id
            )
            result_point_cloud, _ = await FileService.create_point_cloud(
                point_cloud_type=PointCloudType.RECORDING,
                file_data=file_data,
                session=uow.session
            )

            # append extra data you need
            # all in str, otherwise expect errors
            results['tolerance'] = tolerance
            results['project_id'] = str(old_stage.project_id)
            results['old_stage_id'] = str(old_stage.id)
            results['new_stage_id'] = str(new_stage.id)

            # recording result
            results["project_name"] = old_stage.project.name
            results["project_description"] = old_stage.project.description
            results["old_stage_name"] = old_stage.name
            results["old_stage_description"] = old_stage.description
            results["old_stage_start_date"] = (
                old_stage.start_date.isoformat() if old_stage.start_date else None
            )
            results["new_stage_name"] = new_stage.name
            results["new_stage_description"] = new_stage.description
            results["new_stage_start_date"] = (
                new_stage.start_date.isoformat() if new_stage.start_date else None
            )
            result_data = RecordingResultModel(
                project_id=new_stage.project_id,
                data=results,
                type=RecordingResultType.PROGRESS,
                point_cloud_id=result_point_cloud.id)

            recording_result = await RecordingResultService.create_recording_result(
                result_data,
                session=uow.session
            )

            return recording_result.id
    result_id = run_async(run_task())
    return result_id


@celery_app.task(
    base=ProcessingTask
)
def create_recording_result_pdf_report(recording_result_id: UUID, *args, **kwargs) -> UUID:
    """
    Generates a .pdf report for the recording result and stores it.

    The following report will contain:
        - data from the recording result
        - photos from the resulting point cloud

    Returns:
        UUID: ID of the resulting point cloud you might need later
    """
    from airbim_processing import laz_to_images    # type: ignore

    async def run_task():
        async with get_database_uow() as uow:
            recording_result = await RecordingResultService.get_recording_result(
                recording_result_id,
                session=uow.session
            )

            workspace_id = recording_result.project.workspace_id

            # get data
            # it is dict, for real
            data = dict(recording_result.data)

            section_specs = {
                "Сведения о проекте": [
                    ("project_name", "Название"),
                    ("project_description", "Описание"),
                ],
            }

            if recording_result.type == RecordingResultType.PROGRESS:
                section_specs.update({
                    "Старый этап": [
                        ("old_stage_name", "Название"),
                        ("old_stage_description", "Описание"),
                        ("old_stage_start_date", "Дата начала"),
                    ],
                    "Новый этап": [
                        ("new_stage_name", "Название"),
                        ("new_stage_description", "Описание"),
                        ("new_stage_start_date", "Дата начала"),
                    ],
                })
            else:
                section_specs.update({
                    "Этап": [
                        ("stage_name", "Название"),
                        ("stage_description", "Описание"),
                        ("stage_start_date", "Дата начала"),
                    ],
                })

            sections, data = extract_report_sections(data, section_specs)

            # get resulting point cloud
            result_point_cloud = await FileService.get_point_cloud(
                recording_result.point_cloud_id,
                session=uow.session
            )
            # get file
            result_point_cloud_file = result_point_cloud.file

        # title for the report
        title = translate_recording_result_type(recording_result.type)

        with tempfile.TemporaryDirectory() as tmp_dir:
            result_point_cloud_file_path = clean_path(
                os.path.join(tmp_dir, result_point_cloud_file.filename)
            )
            report_path = clean_path(os.path.join(
                tmp_dir, f"{recording_result.type}_report.pdf"))

            # download file
            storage.download_file_locally(
                result_point_cloud_file.key,
                save_path=str(result_point_cloud_file_path)
            )

            # collect images of the result
            photo_paths = laz_to_images(
                laz_path=result_point_cloud_file_path,
                output_dir=tmp_dir
            )

            # append path dir
            # the library provides only names for the files
            photo_paths = [clean_path(os.path.join(tmp_dir, photo_path))
                           for photo_path in photo_paths]

            photos_data = []

            for photo_path in photo_paths:
                # save data
                photo_data = FileService.collect_file_data(photo_path)

                # upload to the storage
                storage.upload_file_locally(photo_data["key"], str(photo_path))

                photo_data = FileModel(
                    filename=photo_data["filename"],
                    key=photo_data["key"],
                    size=photo_data["size"],
                    content_type=photo_data["content_type"],
                    status=FileStatus.UPLOADED,
                    workspace_id=workspace_id
                )

                photos_data.append(photo_data)

            # generate report
            generate_pdf_report(
                title,
                data,
                report_path,
                imgs=photo_paths,
                sections=sections,
            )

            # collect file data
            report_file_data = FileService.collect_file_data(report_path)

            # upload to the storage
            storage.upload_file_locally(
                report_file_data["key"], str(report_path))

        # save everything in the database
        async with get_database_uow() as uow:
            file_data = FileModel(
                filename=report_file_data["filename"],
                key=report_file_data["key"],
                size=report_file_data["size"],
                content_type=report_file_data["content_type"],
                status=FileStatus.UPLOADED,
                workspace_id=workspace_id
            )
            await RecordingResultService.create_pdf_report(
                recording_result_id,
                file_data,
                photos_file_data=photos_data,
                session=uow.session
            )

        return recording_result.point_cloud_id
    result_point_cloud = run_async(run_task())
    return result_point_cloud
