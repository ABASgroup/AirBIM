import uuid
from core.exceptions import NotFoundError
from core.dependencies import get_database_uow, get_storage
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from repositories.files import PointCloudRepository
from utils.convert import convert_point_cloud
from utils.files import get_all_dir_files, delete_file, delete_dir


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

class ConverterTask(celery_app.Task):
    queue = 'converter'

# TODO: separate logic into service


@celery_app.task()
def convert_point_cloud_task(point_cloud_id: uuid.UUID):
    """Converts point cloud into Potree format."""
    service = FileService()
    storage = get_storage()

    async def run_task():
        # we don't want to ruin transaction
        # so make them separate
        async with get_database_uow() as uow:
            # get point cloud
            point_cloud = await FileService.get_point_cloud(point_cloud_id, session=uow.session)
            # check if we already have converted files
            if point_cloud is None:
                raise NotFoundError("Point cloud is not found.")
            if point_cloud.converted_key_prefix:
                # false start up, no actions required
                # don't waste the resources
                return
            await PointCloudRepository.refresh(point_cloud, session=uow.session, relations=["file"])
            file_path = point_cloud.file.filename

        # download point cloud file
        storage.download_file_locally(
            point_cloud.file.key,
            file_path=file_path
        )

        # convert it and save stated save path
        output_path = convert_point_cloud(file_path=file_path)

        # all files in the output dir
        files = get_all_dir_files(output_path)
        prefix = f"converted/{files[0].parent}/"

        for file in files:
            # TODO: make key generation
            key = f"{prefix}{file.name}"
            # upload all of them
            storage.upload_file_locally(key, str(file))

        async with get_database_uow() as uow:
            # save it in the db
            await PointCloudRepository.update_converted_key_prefix(
                point_cloud_id=point_cloud_id,
                prefix=prefix,
                session=uow.session
            )

        # delete downloaded original file
        delete_file(file_path)
        # delete converted files
        delete_dir(output_path)
    run_async(run_task())
