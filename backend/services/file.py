"""Service layer logic for files."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.files import (
    FileUploadConfirmRequest,
    PointCloudFileModel,
    BIMFileModel,
    FileUploadLinkRequest
)

from exceptions.exceptions import NotFoundError

from models.files import PointCloudFile, BimFile, FileStatus

from repositories.files import PointCloudFileRepository, BimFileRepository
from storage import Storage


class FileService:
    def __init__(self):
        pass

    @classmethod
    def create_file_key(
        cls,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        filename: str,
        stage_id: uuid.UUID | None = None
    ):
        """
        Provides a key for the file in the fixed format.

        **Never** create file keys on your own for consistency.
        """
        base = f"workspace_{workspace_id}/project_{project_id}/"
        if stage_id:
            # append stage related part if stage_id is provided
            key = f"{base}stage_{stage_id}/{filename}"
            return key
        return base

    @classmethod
    def clear_stage_files(cls, workspace_id, project_id, stage_id, storage: Storage):
        """Clear all files related to the stage from the storage."""
        prefix = f"workspace_{workspace_id}/project_{project_id}/stage_{stage_id}/"
        storage.delete_files_by_prefix(prefix)

    @classmethod
    def clear_project_files(cls, workspace_id, project_id, storage: Storage):
        """Clear all files related to the project from the storage."""
        prefix = f"workspace_{workspace_id}/project_{project_id}/"
        storage.delete_files_by_prefix(prefix)

    @classmethod
    def clear_workspace_files(cls, workspace_id, storage: Storage):
        """Clear all files related to the workspace from the storage."""
        prefix = f"workspace_{workspace_id}/"
        storage.delete_files_by_prefix(prefix)

    @classmethod
    async def delete_bim_file(cls, project_id: uuid.UUID, storage: Storage, session: AsyncSession):
        """Delete BIM file from the storage and remove entry from the database."""
        try:
            file = await BimFileRepository.get_by_project_id(project_id, session=session)
            if not file:
                raise NotFoundError("BIM file not found for the project.")

            # delete from storage
            storage.delete_file(file.key)

            # delete from database
            await BimFileRepository.delete(file, session=session)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    @classmethod
    async def generate_bim_upload_link(
        cls,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        file_data: FileUploadLinkRequest,
        storage: Storage,
        session: AsyncSession
    ) -> tuple[str, str]:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file key.
        """
        try:
            # create key
            key = cls.create_file_key(
                workspace_id=workspace_id,
                project_id=project_id,
                filename=file_data.filename
            )

            # make pending file
            file_data_db = BIMFileModel(
                filename=file_data.filename,
                key=key,
                content_type=file_data.content_type,
                size=file_data.size,
                project_id=project_id
            )

            await BimFileRepository.create(file_data_db, session=session)

            # generate temporary upload link
            link = storage.get_upload_link(key)

            await session.commit()
            return link, key
        except Exception:
            await session.rollback()
            raise

    @classmethod
    async def confirm_bim_upload(
        cls,
        file_data: FileUploadConfirmRequest,
        storage: Storage,
        session: AsyncSession
    ) -> BimFile:
        """
        Runs checks on the file.

        If everything is fine, returns file entry in DB.
        """
        try:
            # in the database
            # check fields we want to check
            file_db = await BimFileRepository.get_file_by_metadata(
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
            await BimFileRepository.update_status(
                file_db,
                FileStatus.UPLOADED,
                session=session)
            await session.commit()
            return file_db
        except:
            await session.rollback()
            raise

    @classmethod
    async def generate_point_cloud_upload_link(
        cls,
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        stage_id: uuid.UUID,
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
            key = cls.create_file_key(
                workspace_id=workspace_id,
                project_id=project_id,
                filename=file_data.filename,
                stage_id=stage_id
            )

            # make pending file
            file_data_db = PointCloudFileModel(
                filename=file_data.filename,
                key=key,
                content_type=file_data.content_type,
                size=file_data.size,
                stage_id=stage_id
            )

            await PointCloudFileRepository.create(file_data_db, session=session)

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
            file_db = await PointCloudFileRepository.get_file_by_metadata(
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
            await PointCloudFileRepository.update_status(
                file_db,
                FileStatus.UPLOADED,
                session=session)
            await session.commit()
            return file_db
        except:
            await session.rollback()
            raise
