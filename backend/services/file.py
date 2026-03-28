"""Service layer logic for files."""
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.files import (
    FileUploadConfirmRequest,
    PointCloudFileCreate,
    FileUploadLinkRequest
)

from exceptions.exceptions import NotFoundError

from models.files import PointCloudFile, FileStatus

from crud.files import PointCloudFileCRUD
from storage import Storage


class FileService:
    def __init__(self):
        pass

    @classmethod
    def create_file_key(
        cls,
        project_id: int,
        filename: str,
        stage_id: int | None = None
    ):
        """
        Provides a key for the file in the fixed format.

        **Never** create keys on your own for consistency.
        """
        if stage_id:
            key = f"project_{project_id}/stage_{stage_id}/{filename}"
        else:
            key = f"project_{project_id}/{filename}"
        return key

    @classmethod
    def generate_bim_upload_link(cls):
        pass

    @classmethod
    async def generate_point_cloud_upload_link(
        cls,
        project_id: int,
        stage_id: int,
        file_data: FileUploadLinkRequest,
        storage: Storage,
        session: AsyncSession
    ) -> tuple[str, str]:
        """
        Creates presigned URL for point cloud upload and makes reservation in DB.

        Returns url and file key.
        """
        try:
            # create key
            key = cls.create_file_key(project_id=project_id,
                                      filename=file_data.filename,
                                      stage_id=stage_id)

            # make pending file
            file_data_db = PointCloudFileCreate(
                filename=file_data.filename,
                key=key,
                content_type=file_data.content_type,
                size=file_data.size,
                stage_id=stage_id
            )

            await PointCloudFileCRUD.create(file_data_db, session=session)

            # generate temporary upload link
            link = storage.get_upload_link(key)

            await session.commit()
            return link, key
        except Exception:
            await session.rollback()
            raise

    @classmethod
    async def confirm_point_cloud_upload(
        cls,
        stage_id: int,
        file_data: FileUploadConfirmRequest,
        storage: Storage,
        session: AsyncSession
    ) -> PointCloudFile:
        """
        Runs checks on the file.

        If everything is fine, returns file entry in DB.
        """
        try:
            # in the database
            # check fields we want to check
            file_db = await PointCloudFileCRUD.get_file_by_metadata(
                file_data.filename,
                file_data.content_type,
                file_data.size,
                session=session
            )

            if file_db is None:
                raise NotFoundError(
                    "File not found: no entry in the database.")

            # in the storage
            exists = storage.file_exists(file_db.key)
            if not exists:
                raise NotFoundError(
                    "File not found: not uploaded to the storage")

            # everything seems clear, set new status
            await PointCloudFileCRUD.update_status(file_db, FileStatus.UPLOADED, session=session)
            await session.commit()
            return file_db
        except:
            await session.rollback()
            raise
