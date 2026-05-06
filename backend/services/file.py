"""Service layer logic for files."""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.files import (
    FileModel,
    BIMModel,
    FileDataRequest,
    PointCloudModel
)

from core.exceptions import NotFoundError, InvalidFileMetaDataError

from models.file import FileStatus, File, PointCloud
from models.project import Project
from models.stage import Stage

from repositories.files import FileRepository, BimRepository, PointCloudRepository
from repositories.stage import StageRepository
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
    async def clean_up_files(
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

    @staticmethod
    async def delete_file(
        file_id: uuid.UUID,
        session: AsyncSession,
        storage: Storage
    ):
        """Delete file using its ID."""
        file = await FileRepository.get_by_id(file_id, session=session)

        if not file:
            raise NotFoundError("File is not found.")

        # delete file from storage
        storage.delete_file(file.key)
        # delete from storage
        file = await FileRepository.delete(file, session=session)
        return file

    @classmethod
    async def generate_file_download_link(
        cls,
        file_id: uuid.UUID,
        session: AsyncSession,
        storage: Storage
    ) -> str:
        """
        Creates presigned URL for BIM download.

        Returns url and file.
        """
        file = await FileRepository.get_by_id(
            file_id,
            session=session
        )

        if file is None:
            raise NotFoundError(
                "File is not found.")

        link = storage.get_download_link(file.key)

        return link

    @classmethod
    async def confirm_file_upload(
        cls,
        file_id: uuid.UUID,
        file_data: FileDataRequest,
        storage: Storage,
        session: AsyncSession
    ) -> File:
        """
        Runs checks on the file.

        If everything is fine, returns entry in DB.
        """
        # in the database
        file = await FileRepository.get_by_id(file_id, session=session)

        if file is None:
            raise NotFoundError(
                "File not found: no entry about it.")

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
        return file

    @classmethod
    async def create_file(
        cls,
        file_data: FileModel,
        session: AsyncSession,
    ) -> File:
        """
        Creates file entry in the database.
        """
        # make pending file
        file = await FileRepository.create(file_data, session=session)
        return file

    @classmethod
    async def get_file(
        cls,
        file_id: uuid.UUID,
        session: AsyncSession
    ) -> File:
        """Get file entry from the database."""
        file = await FileRepository.get_by_id(file_id, session=session)

        if file is None:
            raise NotFoundError(
                "File not found: no such ID.")

        return file

    @classmethod
    async def get_point_cloud(
        cls,
        point_cloud_id: uuid.UUID,
        session: AsyncSession
    ) -> PointCloud:
        cloud = await PointCloudRepository.get_by_id(point_cloud_id, session=session)

        if cloud is None:
            raise NotFoundError(
                "Point cloud is not found: no such ID.")

        return cloud

    @classmethod
    async def generate_bim_upload_link(
        cls,
        project: Project,
        file_data: FileModel,
        storage: Storage,
        session: AsyncSession
    ) -> str:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file key.
        """
        # make pending file
        file = await cls.create_file(
            file_data=file_data,
            session=session,
        )

        bim = BIMModel(project_id=project.id, file_id=file.id)
        await BimRepository.create(bim, session=session)

        # generate temporary upload link
        link = storage.get_upload_link(file.key)

        return link

    @classmethod
    async def generate_point_cloud_upload_link(
        cls,
        stage: Stage,
        file_data: FileModel,
        storage: Storage,
        session: AsyncSession
    ) -> str:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file key.
        """
        # make pending file
        file = await cls.create_file(
            file_data=file_data,
            session=session,
        )

        cloud = PointCloudModel(stage_id=stage.id, file_id=file.id)
        await PointCloudRepository.create(cloud, session=session)

        # generate temporary upload link
        link = storage.get_upload_link(file.key)

        return link
