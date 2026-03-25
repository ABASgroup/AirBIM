"""Service layer logic for files."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from schemas.files import FileUploadRequest, PointCloudCreate
from crud.files import BimFileCRUD, PointCloudFileCRUD
from storage import Storage


class FileService:
    def __init__(self):
        pass

    @classmethod
    def create_file_key(cls, project_id: int, filename: str):
        """
        Provides a key for the file in the fixed format.

        **Never** create keys on your own for consistency.
        """
        key = f"project_{project_id}/{filename}"
        return key

    @classmethod
    def validate_file_request(cls):
        """
        Runs checks on the file request.
        """
        pass

    @classmethod
    def generate_file_upload_link(
        cls,
        project_id: int,
        file_data: FileUploadRequest,
        storage: Storage
    ):
        # create key
        key = cls.create_file_key(project_id, file_data.filename)

        # generate temporary upload link
        link = storage.get_upload_link(key)

        return link

    @classmethod
    def generate_file_download_link(
        cls,
        project_id: int,
        file_data: FileUploadRequest,
        storage: Storage
    ):
        # create key
        key = cls.create_file_key(project_id, file_data.filename)

        # generate temporary download link
        link = storage.get_download_link(key)

        return link
