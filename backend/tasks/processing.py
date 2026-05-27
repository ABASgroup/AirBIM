import os
import tempfile
from uuid import UUID
from models.file import FileStatus
from schemas.files import FileModel
from utils.files import clean_path, get_file_mime_type, get_file_size
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from core.dependencies import get_database_uow, get_storage
from services.file import FileService
import services.stage as stage_service


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

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

    storage = get_storage()

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

            # save in the storage
            key = FileService.create_file_key(
                filename=output_path.name
            )
            # upload to the storage
            storage.upload_file_locally(key, str(output_path))

            # save in the database
            size = get_file_size(str(output_path.absolute()))
            content_type = get_file_mime_type(str(output_path.absolute()))
            file_data = FileModel(
                filename=output_path.name,
                key=key,
                size=size,
                content_type=content_type,
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
def compare_plan_and_fact(stage_id: UUID):
    import ifcopenshell  # type: ignore
    from airbim_processing import resolve_geo_transform, ifc_to_laz, compute_deviations

    async def run_task():
        pass
