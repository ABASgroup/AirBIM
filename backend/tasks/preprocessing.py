import uuid
from models.file import FileStatus
from core.exceptions import NotFoundError
from core.dependencies import get_database_uow, get_storage
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from schemas.files import FileModel
from repositories.files import PointCloudRepository
from utils.convert import convert_point_cloud
from utils.files import (
    get_all_dir_files,
    delete_file,
    delete_dir,
    get_file_size,
    get_file_mime_type
)


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

class ConverterTask(celery_app.Task):
    queue = 'converter'


@celery_app.task(base=ConverterTask)
def convert_point_cloud_task(point_cloud_id: uuid.UUID):
    """Converts point cloud into Potree format."""
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
                print("ALREADY CONVERTED")
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
        prefix = f"converted{files[0].parent}/".replace("//", "/")

        for file in files:
            # save in the storage
            # TODO: make key generation
            key = f"{prefix}{file.name}"
            # upload all of them
            storage.upload_file_locally(key, str(file))

            # save in the db
            async with get_database_uow() as uow:
                # do we really need to do so?
                file_data = FileModel(
                    filename=file.name,
                    key=key,
                    size=get_file_size(str(file.absolute())),
                    content_type=get_file_mime_type(str(file.absolute())),
                    status=FileStatus.UPLOADED
                )
                await FileService.create_file(file_data, session=uow.session)

        # update prefix
        async with get_database_uow() as uow:
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
