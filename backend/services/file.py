"""Service layer logic for files."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.files import (
    FileUploadConfirmRequest,
    PointCloudFileModel,
    BIMFileModel,
    FileUploadLinkRequest
)

from core.exceptions.exceptions import NotFoundError

from models.files import PointCloudFile, BimFile, FileStatus

from repositories.files import PointCloudFileRepository, BimFileRepository
from infrastructure.storage import Storage


class FileService:
    @staticmethod
    def create_file_key(
        workspace_id: uuid.UUID,
        project_id: uuid.UUID,
        filename: str,
        stage_id: uuid.UUID | None = None
    ) -> str:
        """
        Provides a key for the file in the fixed format.

        **Never** create file keys on your own for consistency.
        """
        key = f"workspace_{workspace_id}/project_{project_id}/"
        if stage_id:
            # append stage related part if stage_id is provided
            key = f"{key}stage_{stage_id}/{filename}"
        else:
            key = f"{key}{filename}"
        return key

    @staticmethod
    def clear_stage_files(workspace_id, project_id, stage_id, storage: Storage):
        """Clear all files related to the stage from the storage."""
        prefix = f"workspace_{workspace_id}/project_{project_id}/stage_{stage_id}/"
        storage.delete_files_by_prefix(prefix)

    @staticmethod
    def clear_project_files(workspace_id, project_id, storage: Storage):
        """Clear all files related to the project from the storage."""
        prefix = f"workspace_{workspace_id}/project_{project_id}/"
        storage.delete_files_by_prefix(prefix)

    @staticmethod
    def clear_workspace_files(workspace_id, storage: Storage):
        """Clear all files related to the workspace from the storage."""
        prefix = f"workspace_{workspace_id}/"
        storage.delete_files_by_prefix(prefix)

    @staticmethod
    async def delete_bim_file(project_id: uuid.UUID, storage: Storage, session: AsyncSession):
        """Delete BIM file from the storage and remove entry from the database."""
        file = await BimFileRepository.get_by_project_id(project_id, session=session)
        if not file:
            raise NotFoundError("BIM file not found for the project.")

        # delete from storage
        storage.delete_file(file.key)

        # delete from database
        await BimFileRepository.delete(file, session=session)

    @classmethod
    async def generate_bim_download_link(
        cls,
        project_id: uuid.UUID,
        session: AsyncSession,
        storage: Storage
    ) -> tuple[str, BimFile]:
        """
        Creates presigned URL for BIM download.

        Returns url and file key.
        """
        # get the key first
        file = await BimFileRepository.get_by_project_id(
            project_id=project_id,
            session=session
        )

        if file is None:
            raise NotFoundError(
                "BIM file for this project is not found")

        link = storage.get_download_link(file.key)

        return link, file

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

        return link, key

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
        return file_db

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

        return link, key

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
        return file_db

    async def clean_up_files(self, storage: Storage, session: AsyncSession):
        """
        Cleans up files from the database and the storage.

        Which files are being cleaned:
        - those, that are pending in the database for a long time but not in the storage
        - those, that are in the storage but not in the database
        """
