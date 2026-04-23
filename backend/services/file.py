"""Service layer logic for files."""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.files import (
    FileModel,
    BIMModel,
    FileDataRequest
)

from core.exceptions import NotFoundError, InvalidFileMetaDataError

from models.file import Bim, FileStatus, File
from models.project import Project

from repositories.files import FileRepository, BimRepository
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
    async def delete_bim(project_id: uuid.UUID, storage: Storage, session: AsyncSession):
        """Delete BIM file from the storage and remove entry from the database."""
        bim = await BimRepository.get_by_project_id(project_id, session=session)

        if not bim:
            raise NotFoundError("BIM is not found for the project.")

        # delete file from storage
        storage.delete_file(bim.file.key)

        # delete from database
        await BimRepository.delete(bim, session=session)
        return bim

    @staticmethod
    def check_file_meta(
        file: File,
        content_type: str,
        size: int,
        filename: str
    ):
        """
        Check provided file metadata with meta that is already in the database.

        You can register there metadata checks you need.
        """
        failed = (file.filename != filename) or (
            file.content_type != content_type) or (file.size != size)

        if failed:
            raise InvalidFileMetaDataError()

    @classmethod
    async def generate_bim_download_link(
        cls,
        project_id: uuid.UUID,
        session: AsyncSession,
        storage: Storage
    ) -> tuple[str, File]:
        """
        Creates presigned URL for BIM download.

        Returns url and file.
        """
        bim = await BimRepository.get_by_project_id(
            project_id=project_id,
            session=session
        )

        if bim is None:
            raise NotFoundError(
                "BIM is not found for the project.")

        link = storage.get_download_link(bim.file.key)

        return link, bim.file

    @classmethod
    async def generate_bim_upload_link(
        cls,
        project: Project,
        file_data: FileDataRequest,
        storage: Storage,
        session: AsyncSession
    ) -> tuple[str, str]:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file key.
        """
        # create key
        key = cls.create_file_key(
            workspace_id=project.workspace_id,
            project_id=project.id,
            filename=file_data.filename
        )

        file = FileModel(
            filename=file_data.filename,
            key=key,
            size=file_data.size,
            content_type=file_data.content_type
        )

        # make pending file
        file = await FileRepository.create(file, session=session)
        bim = BIMModel(project_id=project.id, file_id=file.id)
        await BimRepository.create(bim, session=session)

        # generate temporary upload link
        link = storage.get_upload_link(key)

        return link, key

    @classmethod
    async def confirm_bim_upload(
        cls,
        project_id: uuid.UUID,
        file_data: FileDataRequest,
        storage: Storage,
        session: AsyncSession
    ) -> Bim:
        """
        Runs checks on the file.

        If everything is fine, returns entry in DB.
        """
        # in the database
        bim = await BimRepository.get_by_project_id(project_id, session=session)

        if bim is None:
            raise NotFoundError(
                "BIM is not found for the project.")

        await BimRepository.refresh(bim, session=session, relations=["file"])

        # check fields we want to check
        file = bim.file

        cls.check_file_meta(file, **file_data.model_dump())

        # in the storage
        if not storage.file_exists(file.key):
            raise NotFoundError(
                "File not found: not uploaded to the storage")

        # everything seems clear, set new status
        await FileRepository.update_status(
            file,
            FileStatus.UPLOADED,
            session=session)
        return bim

    @classmethod
    async def clean_up_files(
            cls,
            storage: Storage,
            session: AsyncSession,
            pending_for_limit: timedelta = timedelta(days=1)
    ):
        """
        Cleans up files from the database and the storage.

        Which files are being cleaned:
        - those, that are pending in the database for a long time
        - those, that are in the storage but not in the database
        """
        files_deleted = 0
        # delete files that are pending for far too long
        # they CAN be in the storage if there was no confirm
        # it was decided to delete them anyway
        files = await FileRepository.get_by_status(FileStatus.PENDING, session=session)

        for file in files:
            file_pending_for = datetime.now(timezone.utc) - file.created_at
            if file_pending_for > pending_for_limit:
                # db first
                key = file.key
                await FileRepository.delete(file, session=session)
                storage.delete_file(key)
                files_deleted += 1

        # delete files that are in the storage but not in the database
        # no entry in the database about them is a sign of an "orphan" file
        keys = storage.get_all_keys()
        for key in keys:
            file = await FileRepository.get_by_key(key, session=session)
            if file is None:
                storage.delete_file(key)
                files_deleted += 1
        return files_deleted
