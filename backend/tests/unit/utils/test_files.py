"""Unit tests for utils.files, covering path cleaning, directory/file operations, and MIME type detection."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from utils.files import (
    clean_path,
    delete_dir,
    delete_file,
    get_all_dir_files,
    get_file_mime_type,
    get_file_size,
)


def test_clean_path() -> None:
    """Test if the clean_path correctly resolves absolute path."""
    raw_path = "some/local/dir"
    cleaned = clean_path(raw_path)

    assert isinstance(cleaned, Path)
    assert cleaned.is_absolute()
    assert str(cleaned).endswith("some/local/dir")


def test_get_all_dir_files(tmp_path: Path) -> None:
    """Test reading files from a directory."""
    # Create temp files
    file1 = tmp_path / "test1.txt"
    file1.touch()

    file2 = tmp_path / "test2.laz"
    file2.touch()

    # Create a nested directory to ensure it is skipped (get_all_dir_files targets only files)
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()

    files = get_all_dir_files(str(tmp_path))

    assert len(files) == 2
    assert file1.absolute() in files
    assert file2.absolute() in files
    assert nested_dir.absolute() not in files


def test_delete_dir(tmp_path: Path) -> None:
    """Test directory recursive deletion."""
    test_dir = tmp_path / "target_dir"
    test_dir.mkdir()

    nested_file = test_dir / "file.txt"
    nested_file.touch()

    assert test_dir.exists()

    delete_dir(str(test_dir))

    assert not test_dir.exists()
    assert not nested_file.exists()


def test_delete_file(tmp_path: Path) -> None:
    """Test single file deletion."""
    test_file = tmp_path / "to_delete.txt"
    test_file.touch()

    assert test_file.exists()
    delete_file(str(test_file))
    assert not test_file.exists()

    # Ensure it doesn't fail if file does not exist
    delete_file(str(test_file))


def test_get_file_size(tmp_path: Path) -> None:
    """Test retrieving file size."""
    test_file = tmp_path / "content.txt"
    test_file.write_text("Hello, World!")  # 13 bytes

    size = get_file_size(str(test_file))
    assert size == 13


def test_get_file_mime_type_ifc(tmp_path: Path) -> None:
    """Test IFC file mime type detection via signature header."""
    ifc_file = tmp_path / "model.ifc"
    # ISO-10303-21 signature
    ifc_file.write_bytes(b"ISO-10303-21;HEADER;...")

    mime_type = get_file_mime_type(str(ifc_file))
    assert mime_type == "application/x-ifc"


def test_get_file_mime_type_las(tmp_path: Path) -> None:
    """Test LAS/LAZ file mime type detection via signature header."""
    las_file = tmp_path / "scan.laz"
    # LASF signature
    las_file.write_bytes(b"LASF\x00\x00\x00...")

    mime_type = get_file_mime_type(str(las_file))
    assert mime_type == "application/octet-stream"


@patch("utils.files.Magika")
def test_get_file_mime_type_magika_fallback(
    MockMagika: MagicMock, tmp_path: Path
) -> None:
    """Test Magika fallback for other file formats. Without actual Magika dependency, we mock its behavior."""
    # Configure mock
    mock_instance = MockMagika.return_value
    mock_result = MagicMock()
    mock_result.output.mime_type = "image/png"
    mock_instance.identify_path.return_value = mock_result

    png_file = tmp_path / "image.png"
    # Random bytes, no IFC/LASF signature
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n...")

    mime_type = get_file_mime_type(str(png_file))

    assert mime_type == "image/png"
    mock_instance.identify_path.assert_called_once_with(clean_path(str(png_file)))
