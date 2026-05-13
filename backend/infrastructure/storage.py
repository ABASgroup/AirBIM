"""App storage for files"""
from typing import BinaryIO
import boto3
from botocore.exceptions import ClientError
from core.configs.storage import storage_config


class Storage:
    """
    App S3 storage.

    Interface to interact with the S3 storage.
    """

    def __init__(self):
        """Establish connection to the storage"""
        self._resource = boto3.resource(
            "s3",
            endpoint_url=storage_config.endpoint,
            aws_access_key_id=storage_config.STORAGE_ACCESS_KEY_ID,
            aws_secret_access_key=storage_config.STORAGE_SECRET_KEY,
        )
        self._client = self._resource.meta.client
        self._bucket_name = storage_config.STORAGE_BUCKET
        self._url_expiration_time = storage_config.STORAGE_URL_EXP_TIME

        # create bucket only if it doesn't exists
        # safe measure
        if not self._bucket_exists():
            self._client.create_bucket(Bucket=self._bucket_name)

    def _bucket_exists(self):
        """Check if storage bucket exists."""
        try:
            self._client.head_bucket(Bucket=self._bucket_name)
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
        response = self._client.upload_fileobj(file, self._bucket_name, key)
        return response

    def download_file_object(self, key: str) -> BinaryIO:
        """
        Download file from the storage.

        Utilizes a lot of resources of the server you use, so
        use with small files or when you can handle the load.

        Args:
            key (str): key/path of the file in the storage
        """
        response = self._client.get_object(Bucket=self._bucket_name, Key=key)
        content = response['Body']
        return content

    def upload_file_locally(self, key: str, file_path: str):
        """
        Upload file to the storage from the local dir.

        Args:
            key (str): key/path of the file in the storage
            file_path (str): path to the file
        """
        self._client.upload_file(
            Filename=file_path,
            Bucket=self._bucket_name,
            Key=key
        )

    def download_file_locally(self, key: str, save_path: str):
        """
        Download file from the storage.

        Saves it locally.

        Args:
            key (str): key/path of the file in the storage
            save_path (str): save path of the file
        """
        self._client.download_file(self._bucket_name, key, save_path)

    def get_upload_link(self, key: str):
        """
        Get temporary link for uploading file to the storage

        Args:
            key (str): key/path of the file in the storage
        """
        url = self._client.generate_presigned_url(
            ClientMethod='put_object',
            Params={'Bucket': self._bucket_name, 'Key': key},
            ExpiresIn=self._url_expiration_time
        )
        return url

    def get_download_link(self, key: str) -> str:
        """
        Get temporary link for downloading file to the storage.

        Args:
            key (str): key/path of the file in the storage
        """
        url = self._client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': self._bucket_name, 'Key': key},
            ExpiresIn=self._url_expiration_time
        )
        return url

    def get_all_keys(self) -> list[str]:
        """Get all keys in the bucket."""
        bucket = self._resource.Bucket(self._bucket_name)
        return [obj.key for obj in bucket.objects.all()]

    def get_keys_with_prefix(self, prefix: str) -> list[str]:
        """
        Get temporary link for downloading file to the storage.

        Args:
            prefix (str): key prefix of the files you need
        """
        bucket = self._resource.Bucket(self._bucket_name)

        keys = []

        for obj in bucket.objects.filter(Prefix=prefix):
            keys.append(obj.key)

        return keys

    def delete_files_by_prefix(self, prefix: str) -> int:
        """
        Delete all files that contain the provided prefix.

        Returns the amount of files deleted.

        Args:
            prefix (str): key prefix of the files you want to delete
        """
        if not prefix.endswith("/"):
            prefix += "/"

        bucket = self._resource.Bucket(self._bucket_name)

        keys_to_delete = [{'Key': obj.key}
                          for obj in bucket.objects.filter(Prefix=prefix)]

        if not keys_to_delete:
            return 0

        response = bucket.delete_objects(
            Delete={
                'Objects': keys_to_delete,
                'Quiet': False
            }
        )

        if 'Errors' in response:
            for error in response['Errors']:
                print(f"Error {error['Key']}: {error['Code']}")

        return len(keys_to_delete)

    def delete_file(self, key: str):
        """
        Delete file from the storage.

        Args:
            key (str): key/path of the file in the storage
        """
        response = self._client.delete_object(
            Bucket=self._bucket_name, Key=key)
        return response

    def delete_files(self, keys: list[str]):
        """
        Delete files from the storage.

        Args:
            keys (list[str]): keys/paths of the files in the storage
        """
        # format to S3 API
        all_objects = [{'Key': key} for key in keys]

        # batch deletion (1000 is the maximum)
        batch_size = 1000
        for i in range(0, len(all_objects), batch_size):
            batch = all_objects[i:i + batch_size]
            response = self._client.delete_objects(
                Bucket=self._bucket_name,
                Delete={
                    'Objects': batch,
                    'Quiet': True
                }
            )

    def file_exists(self, key: str) -> bool:
        """
        Checks if a file with this key exists.

        Args:
            key (str): key/path of the file in the storage
        """
        try:
            self._client.head_object(Bucket=self._bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                # something's wrong
                raise
