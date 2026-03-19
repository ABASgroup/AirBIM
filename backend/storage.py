"""App storage for files"""
import boto3
from botocore.exceptions import ClientError
from typing import BinaryIO
from config import storage_config


class Storage:
    def __init__(self):
        """Establish connection to the storage"""
        self.client = boto3.client(
            "s3",
            endpoint_url=storage_config.endpoint,
            aws_access_key_id=storage_config.STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=storage_config.STORAGE_SECRET_KEY,
        )
        self.bucket_name = storage_config.STORAGE_BUCKET
        self.url_expiration_time = storage_config.STORAGE_URL_EXP_TIME

        # create bucket only if it doesn't exists
        if not self._bucket_exists():
            self.client.create_bucket(Bucket=self.bucket_name)

    def _bucket_exists(self):
        """Check if storage bucket exists"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # bucket does not exist
                return False
            elif error_code == 403:
                # bucket exists but you don't have access
                return True
            else:
                # unexpected error
                raise

    def upload_file_object(self, file: BinaryIO, key: str):
        """
        Save file in the storage.

        Utilizes a lot of resources of the server you use, so
        use with small files or when you can handle the load.

        Args:
            file (BinaryIO): binary file object
            prefix (str): prefix for the save path (added to filename)
            filename (str): name you want to use for the file
        """
        response = self.client.upload_fileobj(file, self.bucket_name, key)
        return response

    def download_file_object(self, key: str) -> BinaryIO:
        """
        Download file from the storage.

        Utilizes a lot of resources of the server you use, so
        use with small files or when you can handle the load.

        Args:
            key (str): key/path of the file in the storage
        """
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        content = response['Body']
        return content

    def get_upload_link(self, key: str):
        """Get temporary link for uploading file to the storage"""
        url = self.client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=self.url_expiration_time
        )
        return url

    def get_download_link(self, key: str):
        """Get temporary link for downloading file to the storage"""
        url = self.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': self.bucket_name, 'Key': key},
            ExpiresIn=self.url_expiration_time
        )
        return url

    def delete_file(self, key: str):
        """
        Delete file from the storage.

        Args:
            key (str): key/path of the file in the storage
        """
        response = self.client.delete_object(Bucket=self.bucket_name, Key=key)
        return response
