import pathlib
import shutil
import os
from magika import Magika


def get_all_dir_files(path: str) -> list[pathlib.Path]:
    """Returns list of file paths in the directory."""
    files = []

    directory = clean_path(path)
    for item in directory.iterdir():
        # only files
        if item.is_file():
            files.append(item)
    return files


def clean_path(path: str) -> pathlib.Path:
    """
    Makes path safe and clear so it would not break anything.

    Also turns path into absolute path.
    """
    return pathlib.Path(fr"{path}").absolute()


def delete_dir(path: str):
    """
    Delete dir and all its content (files and dirs).

    If dir wasn't found it would not raise.
    """
    directory = clean_path(path)
    if os.path.exists(directory):
        shutil.rmtree(directory)


def delete_file(path: str):
    """
    Delete file.

    If dir wasn't found it would not raise.
    """
    cleaned_path = clean_path(path)
    if os.path.isfile(cleaned_path):
        os.remove(cleaned_path)


def get_file_size(path: str) -> int:
    """Get file size in bytes."""
    file_path = clean_path(path)
    size = file_path.stat().st_size
    return size


def get_file_mime_type(path: str) -> str:
    """Get file mime type (or content type)."""
    file_path = clean_path(path)

    # read manually to define type
    # that we typically expect
    with open(file_path, "rb") as f:
        header = f.read(15)

    if header.startswith(b"ISO-10303-21"):
        return "application/x-ifc"
    if header.startswith(b"LASF"):
        return "application/octet-stream"

    # use tool to autodetect type
    magika = Magika()
    result = magika.identify_path(file_path)

    return result.output.mime_type