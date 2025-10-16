import os
import json
import subprocess
import rasterio
import logging

logger = logging.getLogger(__name__)


def convert_las_to_laz(las_path, output_path=None):
    """
    Конвертирует LAS файл в LAZ формат используя PDAL

    :param las_path: Путь к исходному LAS файлу
    :param output_path: Путь для сохранения LAZ (если None, создается автоматически)
    :return: Путь к созданному LAZ файлу
    """
    if output_path is None:
        base = os.path.splitext(las_path)[0]
        output_path = base + ".laz"

    try:
        # Используем PDAL для конвертации
        subprocess.run(
            ["pdal", "translate", las_path, output_path],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Converted {las_path} to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to convert LAS to LAZ: {e.stderr}")
        raise Exception(f"LAS to LAZ conversion failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception(
            "PDAL is not installed. Please install it to use LAS/LAZ conversion."
        )


def get_pointcloud_info(file_path):
    """
    Получает информацию об облаке точек используя PDAL

    :param file_path: Путь к LAZ/LAS файлу
    :return: Словарь с метаданными
    """
    try:
        result = subprocess.run(
            ["pdal", "info", "--summary", file_path],
            check=True,
            capture_output=True,
            text=True,
        )

        info = json.loads(result.stdout)
        summary = info.get("summary", {})

        # Извлекаем ключевую информацию
        metadata = {
            "point_count": summary.get("num_points", 0),
            "bounds": summary.get("bounds", {}),
            "dimensions": [dim for dim in summary.get("dimensions", [])],
            "srs": info.get("srs", {}).get("wkt", None),
        }

        return metadata
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get point cloud info: {e.stderr}")
        raise Exception(f"Failed to get point cloud info: {e.stderr}")
    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse PDAL output: {str(e)}")
        raise Exception(f"Failed to parse point cloud info: {str(e)}")


def get_geotiff_info(file_path):
    """
    Получает информацию о GeoTIFF файле используя rasterio

    :param file_path: Путь к GeoTIFF файлу
    :return: Словарь с метаданными
    """
    try:
        with rasterio.open(file_path) as src:
            metadata = {
                "width": src.width,
                "height": src.height,
                "bands": src.count,
                "crs": src.crs.to_string() if src.crs else None,
                "bounds": {
                    "minx": src.bounds.left,
                    "miny": src.bounds.bottom,
                    "maxx": src.bounds.right,
                    "maxy": src.bounds.top,
                },
                "resolution": src.res,
                "dtype": str(src.dtypes[0]),
                "nodata": src.nodata,
            }

        return metadata
    except Exception as e:
        logger.error(f"Failed to get GeoTIFF info: {str(e)}")
        raise Exception(f"Failed to get GeoTIFF info: {str(e)}")


def validate_file_type(file, expected_extensions):
    """
    Валидирует тип загружаемого файла

    :param file: Загруженный файл
    :param expected_extensions: Список допустимых расширений файла
    :return: True если валидация прошла
    """
    filename = file.name.lower()
    return any(filename.endswith(ext) for ext in expected_extensions)
