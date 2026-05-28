import os
from dataclasses import asdict
import tempfile
from uuid import UUID
from models.file import FileStatus, PointCloudType
from models.recording_result import RecordingResultType
from schemas.file import FileModel
from schemas.recording_result import RecordingResultModel
from utils.files import clean_path
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from core.dependencies import get_database_uow, get_storage
from services.file import FileService
import services.stage as stage_service
from services.recording_result import RecordingResultService


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

storage = get_storage()


class ProcessingTask(celery_app.Task):
    queue = 'processing'


@celery_app.task(base=ProcessingTask)
def convert_bim_to_point_cloud(bim_id: UUID):
    # lazy imports so your main app would work
    import ifcopenshell  # type: ignore
    from airbim_processing import resolve_geo_transform, ifc_to_laz, compute_deviations  # type: ignore

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
            output_path = clean_path(tmp_dir) / f"{file_path.stem}.laz"

            # download bim file
            storage.download_file_locally(
                bim.file.key,
                save_path=str(file_path)
            )

            # convert
            bim_data = ifcopenshell.open(file_path)
            geo_result = resolve_geo_transform(bim_data)

            result = ifc_to_laz(
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
                await FileService.save_converted_bim_file(
                    bim.id,
                    file_data=file_data,
                    session=uow.session
                )

    run_async(run_task())


@celery_app.task(base=ProcessingTask)
def compare_scan_and_plan(stage_id: UUID, tolerance: float = 0.05):
    from airbim_processing import compute_deviations    # type: ignore

    async def run_task():
        async with get_database_uow() as uow:
            # get stage and its point cloud
            stage = await stage_service.get_stage(stage_id, session=uow.session)
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
            output_path = clean_path(tmp_dir) / f"{stage_id}.laz"

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
                result_data = RecordingResultModel(
                    project_id=stage.project_id,
                    data=results,
                    type=RecordingResultType.PLAN_FACT,
                    point_cloud_id=result_point_cloud.id)

                recording_result = await RecordingResultService.create_recording_result(
                    result_data,
                    session=uow.session
                )

            return recording_result
    result = run_async(run_task())
    print(result.id)
