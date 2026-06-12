"""Tests for the Storage class in the infrastructure layer."""

from io import BytesIO
from pathlib import Path

import pytest
from botocore.exceptions import ClientError

from infrastructure.storage import Storage


@pytest.mark.asyncio
async def test_storage_bucket_exists(storage: Storage) -> None:
    """Storage should correctly check if bucket exists."""
    assert storage._bucket_exists() is True, "Bucket should exist"  # pylint: disable=protected-access


@pytest.mark.asyncio
async def test_storage_can_upload_and_download_file(
    storage: Storage, test_building_ifc_path: Path, tmp_path: Path
) -> None:
    """Storage should be able to upload and download files."""
    key = "test-storage"
    storage.upload_file_locally(key, str(test_building_ifc_path))

    assert storage.file_exists(key), "File should exist in storage after upload"

    download_path = tmp_path / "downloaded_test_building.ifc"
    storage.download_file_locally(key, str(download_path))

    assert download_path.is_file(), "Downloaded file does not exist"
    assert download_path.stat().st_size > 0, "Downloaded file is empty"
    assert (
        download_path.read_bytes() == test_building_ifc_path.read_bytes()
    ), "Downloaded file content does not match original"


@pytest.mark.asyncio
async def test_storage_can_upload_and_download_file_object(
    storage: Storage, test_building_ifc_path: Path
) -> None:
    """Storage should be able to upload and download file objects."""
    key = "test-storage-object"
    with test_building_ifc_path.open("rb") as file:
        storage.upload_file_object(file, key)

    downloaded_content = storage.download_file_object(key).read()
    assert (
        downloaded_content == test_building_ifc_path.read_bytes()
    ), "Downloaded file content does not match original"


@pytest.mark.asyncio
async def test_storage_download_nonexistent_file(storage: Storage) -> None:
    """Storage should raise an error when trying to download a non-existent file."""
    key = "nonexistent-file"
    with pytest.raises(ClientError):
        storage.download_file_locally(key, "should_not_be_created.txt")
    with pytest.raises(ClientError):
        _ = storage.download_file_object(key)


@pytest.mark.asyncio
async def test_storage_can_get_keys(storage: Storage) -> None:
    """Storage should be able to list keys in the bucket and use prefix."""
    keys = ["test-key-1", "test-key-2", "test-key-3"]
    extra_keys = ["extra-key-1", "extra-key-2"]
    keys.extend(extra_keys)

    for key in keys:
        storage.upload_file_object(BytesIO(b"test content"), key)

    retrieved_keys = storage.get_all_keys()
    for key in keys:
        assert (
            key in retrieved_keys
        ), f"Key {key} should be in the list of retrieved keys"

    extra_retrieved_keys = storage.get_keys_with_prefix("extra-")
    for key in extra_keys:
        assert (
            key in extra_retrieved_keys
        ), f"Key {key} should be in the list of retrieved keys with prefix 'extra-'"


@pytest.mark.asyncio
async def test_storage_can_delete_files(
    storage: Storage, test_building_ifc_path: Path
) -> None:
    """Storage should be able to delete files."""
    keys = ["delete-test-key-1", "delete-test-key-2"]
    extra_keys = ["extra1-delete-key", "extra2-delete-key-1", "extra2-delete-key-2"]
    for key in keys + extra_keys:
        storage.upload_file_locally(key, str(test_building_ifc_path))
        assert storage.file_exists(
            key
        ), f"Key {key} should exist in storage after upload"

    storage.delete_files(keys)
    for key in extra_keys:
        assert storage.file_exists(
            key
        ), f"Key {key} should still exist in storage after deleting other keys"
    for key in keys:
        assert (
            key not in storage.get_all_keys()
        ), f"Key {key} should have been deleted from storage"
        assert not storage.file_exists(
            key
        ), f"Key {key} should have been deleted from storage"

    storage.delete_file(extra_keys[0])
    assert not storage.file_exists(
        extra_keys[0]
    ), f"Key {extra_keys[0]} should have been deleted from storage"

    storage.delete_files_by_prefix("extra2")
    for key in extra_keys[1:]:
        assert not storage.file_exists(
            key
        ), f"Key {key} should have been deleted from storage"
