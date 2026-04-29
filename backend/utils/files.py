import pathlib
import shutil
import os


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
    if os.path.exists(path):
        shutil.rmtree(path)


def delete_file(path: str):
    """
    Delete file.

    If dir wasn't found it would not raise.
    """
    if os.path.isfile(path):
        os.remove(path)
