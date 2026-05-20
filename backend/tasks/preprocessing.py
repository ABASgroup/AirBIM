import uuid
import tempfile
import os
from models.file import FileStatus
from core.dependencies import get_database_uow, get_storage
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from schemas.files import FileModel
from utils.convert import convert_point_cloud
from utils.files import (
    get_all_dir_files,
    get_file_size,
    get_file_mime_type,
    clean_path
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
        async with get_database_uow() as uow:
            # get point cloud
            point_cloud = await FileService.get_point_cloud(point_cloud_id, session=uow.session)
            # check if we already have converted files
            converted_files = await FileService.get_converted_point_cloud_files(point_cloud_id, session=uow.session)
            if len(converted_files):
                # false start up, no actions required
                # don't waste the resources
                print("ALREADY CONVERTED")
                return
            point_cloud_file = await FileService.get_file(point_cloud.file_id, session=uow.session)

        # all in temp_dir will be deleted after its done
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = clean_path(os.path.join(
                tmp_dir, point_cloud_file.filename))
            output_path = clean_path(tmp_dir)

            # download point cloud file
            storage.download_file_locally(
                point_cloud_file.key,
                save_path=str(file_path)
            )

            # convert it and save stated save path
            output_path = convert_point_cloud(
                file_path=str(file_path),
                output_path=str(output_path)
            )

            # all files in the output dir
            file_dir = get_all_dir_files(output_path)

            files = {}

            for file in file_dir:
                # save in the storage
                key = FileService.create_file_key(
                    filename=file.name
                )

                # upload to the storage
                storage.upload_file_locally(key, str(file))

                size = get_file_size(str(file.absolute()))
                content_type = get_file_mime_type(str(file.absolute()))
                file_data = FileModel(
                    filename=file.name,
                    key=key,
                    size=size,
                    content_type=content_type,
                    status=FileStatus.UPLOADED,
                    workspace_id=point_cloud_file.workspace_id
                )

                files[str(file)] = file_data

            for file_path, data in files.items():
                # save in the db
                async with get_database_uow() as uow:
                    await FileService.save_converted_point_cloud_file(
                        point_cloud_id,
                        file_data=data,
                        session=uow.session
                    )
                # save in the storage
                storage.upload_file_locally(data.key, file_path)

    run_async(run_task())
