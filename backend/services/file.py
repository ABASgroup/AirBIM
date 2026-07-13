"""Service layer logic for files."""
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from utils.files import get_file_size, get_file_mime_type
from schemas.file import (
    FileModel,
    BIMModel,
    FileDataRequest,
    PointCloudModel,
    PointCloudConvertedModel,
)

from core.exceptions import NotFoundError, InvalidFileMetaDataError, AlreadyExistsError

from models.file import FileStatus, File, PointCloud, BIM, PointCloudType

from repositories.files import (
    FileRepository,
    BIMRepository,
    PointCloudRepository,
    PointCloudConvertedRepository,
)
from infrastructure.storage import Storage


class FileService:
    @staticmethod
    def create_file_key(
        filename: str,
    ) -> str:
        """
        Provides a key (unique) for the file in the fixed format.

        **Never** create file keys on your own for consistency.
        """
        key = f"{filename}_{uuid.uuid4()}/{filename}"
        return key

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
        keys_to_delete = set()

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
                keys_to_delete.add(key)

        # delete files that are in the storage but not in the database
        # no entry in the database about them is a sign of an "orphan" file
        # usually there is always db and then storage
        keys = storage.get_all_keys()
        db_keys = set(await FileRepository.get_all_keys(session=session))

        for key in keys:
            if key not in db_keys:
                keys_to_delete.add(key)

        storage.delete_files(list(keys_to_delete))
        files_deleted = len(keys_to_delete)
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
    def collect_file_data(
        cls,
        path: Path
    ) -> dict:
        """
        Collects file data of a local file.

        Returns dict with filename, key, size and content type.
        """
        key = cls.create_file_key(
            filename=path.name
        )
        size = get_file_size(str(path.absolute()))
        content_type = get_file_mime_type(str(path.absolute()))

        return {
            "filename": path.name,
            "key": key,
            "size": size,
            "content_type": content_type,
            "path": path
        }

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

        # you can't confirm files that are not pending
        if file.status != FileStatus.PENDING:
            raise AlreadyExistsError("file")

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
        file = await FileRepository.create(file_data.model_dump(exclude_unset=True), session=session)
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
        cloud = await PointCloudRepository.get_by_id(point_cloud_id, relations=["file"], session=session)

        if cloud is None:
            raise NotFoundError(
                "Point cloud is not found: no such ID.")

        return cloud

    @classmethod
    async def get_point_cloud_by_file_id(
        cls,
        file_id: uuid.UUID,
        session: AsyncSession
    ) -> PointCloud | None:
        """Get point cloud by the underlying file ID, if it exists."""
        return await PointCloudRepository.get_by_file_id(file_id, session=session)

    @classmethod
    async def get_bim(
        cls,
        bim_id: uuid.UUID,
        session: AsyncSession
    ) -> BIM:
        bim = await BIMRepository.get_by_id(bim_id, relations=["file"], session=session)

        if bim is None:
            raise NotFoundError(
                "BIM is not found: no such ID.")

        return bim

    @classmethod
    async def get_bim_by_file_id(
        cls,
        file_id: uuid.UUID,
        session: AsyncSession
    ) -> BIM | None:
        """Get BIM by the underlying file ID, if it exists."""
        bim = await BIMRepository.get_by_file_id(file_id, session=session)

        if bim is None:
            raise NotFoundError(
                "BIM is not found: no file with such ID.")

        return bim

    @classmethod
    async def get_bim_by_project_id(
        cls,
        project_id: uuid.UUID,
        session: AsyncSession
    ) -> BIM:
        """Get BIM by the project it is connected to."""
        bim = await BIMRepository.get_by_project_id(project_id, session=session)

        if bim is None:
            raise NotFoundError(
                "BIM is not found: no project with such ID.")

        return bim

    @classmethod
    async def generate_bim_upload_link(
        cls,
        project_id: uuid.UUID,
        file_data: FileModel,
        storage: Storage,
        session: AsyncSession
    ) -> tuple[str, File]:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file.
        """
        # make pending file
        file = await cls.create_file(
            file_data=file_data,
            session=session,
        )

        bim = BIMModel(project_id=project_id, file_id=file.id)
        await BIMRepository.create(bim.model_dump(exclude_unset=True), session=session)

        # generate temporary upload link
        link = storage.get_upload_link(file.key)

        return link, file

    @classmethod
    async def generate_point_cloud_upload_link(
        cls,
        stage_id: uuid.UUID,
        file_data: FileModel,
        storage: Storage,
        session: AsyncSession
    ) -> tuple[str, File]:
        """
        Creates presigned URL for BIM upload and makes reservation in DB.

        Returns url and file.
        """
        # make pending file
        file = await cls.create_file(
            file_data=file_data,
            session=session,
        )

        cloud = PointCloudModel(stage_id=stage_id, file_id=file.id)
        await PointCloudRepository.create(cloud.model_dump(exclude_unset=True), session=session)

        # generate temporary upload link
        link = storage.get_upload_link(file.key)

        return link, file

    @classmethod
    async def save_converted_bim_file(
        cls,
        bim_id: uuid.UUID,
        file_data: FileModel,
        session: AsyncSession
    ):
        """Saves converted point cloud you've got from the BIM."""
        # create file first
        file = await cls.create_file(file_data, session=session)

        # create point cloud record
        data = PointCloudModel(
            file_id=file.id,
            type=PointCloudType.PLAN
        )
        point_cloud = await PointCloudRepository.create(data.model_dump(exclude_unset=True), session=session)

        # set a connection
        bim = await cls.get_bim(bim_id, session=session)
        await BIMRepository.set_point_cloud(bim=bim, point_cloud_id=point_cloud.id, session=session)

        return point_cloud.id

    @classmethod
    async def save_bim_preview_file(
        cls,
        bim_id: uuid.UUID,
        file_data: FileModel,
        session: AsyncSession
    ):
        """Saves preview image file for the BIM."""
        file = await cls.create_file(file_data, session=session)

        bim = await cls.get_bim(bim_id, session=session)
        await BIMRepository.set_preview_file(
            bim=bim, preview_file_id=file.id, session=session
        )

        return file.id

    @classmethod
    async def save_converted_point_cloud_file(
        cls,
        point_cloud_id: uuid.UUID,
        file_data: FileModel,
        session: AsyncSession
    ):
        """Saves converted file in the database and creates connection."""
        # create files first
        file = await cls.create_file(file_data, session=session)

        # then connection
        data = PointCloudConvertedModel(
            point_cloud_id=point_cloud_id,
            file_id=file.id
        )
        await PointCloudConvertedRepository.create(data.model_dump(exclude_unset=True), session=session)

    @classmethod
    async def get_converted_point_cloud_files(
        cls,
        point_cloud_id: uuid.UUID,
        session: AsyncSession
    ) -> list[File]:
        """Get all files for a converted point cloud."""
        records = await PointCloudConvertedRepository.get_by_point_cloud_id(
            point_cloud_id=point_cloud_id,
            session=session
        )

        files = []

        for record in records:
            files.append(record.file)

        return files

    @classmethod
    async def create_point_cloud(
        cls,
        point_cloud_type: PointCloudType,
        file_data: FileModel,
        session: AsyncSession,
        stage_id: uuid.UUID | None = None
    ) -> tuple[PointCloud, File]:
        """Creates point cloud entry in the database and its file."""
        file = await cls.create_file(file_data, session=session)

        cloud_data = PointCloudModel(
            stage_id=stage_id,
            file_id=file.id,
            type=point_cloud_type
        )

        # we don't need to store stage_id for some types
        if point_cloud_type in [PointCloudType.RECORDING, PointCloudType.PLAN]:
            cloud_data.stage_id = None

        cloud_data.file_id = file.id
        cloud = await PointCloudRepository.create(cloud_data.model_dump(exclude_unset=True), session=session)
        return cloud, file

    @classmethod
    async def create_bim(
        cls,
        bim_data: BIMModel,
        file_data: FileModel,
        session: AsyncSession
    ) -> tuple[BIM, File]:
        """Creates BIM entry in the database and its file."""
        file = await cls.create_file(file_data, session=session)
        bim_data.file_id = file.id
        bim = await BIMRepository.create(bim_data.model_dump(exclude_unset=True), session=session)
        return bim, file
