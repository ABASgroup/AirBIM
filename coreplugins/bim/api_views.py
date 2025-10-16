import os
import time
import requests
import logging
from os import path
from enum import Enum
from itertools import chain as iter_chain

from app.plugins.views import TaskView
from app.plugins.worker import run_function_async
from app.plugins.data_store import GlobalDataStore
from app.plugins import signals as plugin_signals
from app.models import BIMFile

from worker.celery import app
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from rest_framework.fields import ChoiceField, CharField, JSONField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from .utils.file_utils import (
    validate_file_type,
    convert_las_to_laz,
    get_geotiff_info,
    get_pointcloud_info,
)

logger = logging.getLogger(__name__)


class UploadFileView(TaskView):
    """API для загрузки LAS/LAZ и GeoTIFF файлов"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if "file" not in request.FILES:
            return Response(
                {"error": "Файл не был передан"}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]

        if not validate_file_type(uploaded_file, [".las", ".laz", ".tif", ".tiff"]):
            return Response(
                {"error": "Неподдерживаемый тип файла. Допустимы: LAZ, LAS или GeoTIFF"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = uploaded_file.name.split(".")[-1].upper()
        if extension in ["TIF", "TIFF"]:
            file_type = "GEOTIFF"
        else:
            file_type = extension

        # Читаем содержимое файла из временного пути (файл уже закрыт кастомным upload handler)
        print(f"[BIM] Reading uploaded file", flush=True)
        try:
            # Проверяем, есть ли метод temporary_file_path (для закрытых временных файлов)
            if hasattr(uploaded_file, 'temporary_file_path'):
                temp_file_path = uploaded_file.temporary_file_path()
                print(f"[BIM] Reading from temporary file: {temp_file_path}", flush=True)
                with open(temp_file_path, 'rb') as f:
                    file_content = f.read()
            else:
                # Для файлов в памяти
                print(f"[BIM] Reading from memory", flush=True)
                file_content = uploaded_file.read()
            
            print(f"[BIM] File read successfully, size: {len(file_content)} bytes", flush=True)
        except Exception as e:
            print(f"[BIM ERROR] Failed to read file: {str(e)}", flush=True)
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Не удалось прочитать файл: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Сначала создаем запись в БД без сохранения, чтобы получить ID
            bim_file = BIMFile(
                user=request.user,
                file_type=file_type,
                original_filename=uploaded_file.name,
                size=uploaded_file.size,
            )
            # Первое сохранение для получения ID
            bim_file.save()

            # Формируем путь: MEDIA_ROOT/bim/user_<id>/<type>/<file_id>/
            file_dir = os.path.join(
                settings.MEDIA_ROOT,
                "bim",
                f"user_{request.user.id}",
                file_type.lower(),
                str(bim_file.id),
            )
            os.makedirs(file_dir, exist_ok=True)

            # Если файл LAS, конвертируем его в LAZ
            if file_type == "LAS":
                temp_las_path = os.path.join(file_dir, "temp.las")
                print(f"[BIM] Saving LAS file for conversion", flush=True)
                with open(temp_las_path, "wb+") as destination:
                    destination.write(file_content)
                
                final_filename = os.path.splitext(uploaded_file.name)[0] + ".laz"
                final_path = os.path.join(file_dir, final_filename)
                print(f"[BIM] Converting LAS to LAZ", flush=True)
                convert_las_to_laz(temp_las_path, final_path)
                os.remove(temp_las_path)
                print(f"[BIM] LAS converted to LAZ successfully", flush=True)
            else:
                final_filename = uploaded_file.name
                final_path = os.path.join(file_dir, final_filename)
                print(f"[BIM] Saving file: {final_filename} to {final_path}", flush=True)
                
                # Записываем содержимое файла, которое мы прочитали ранее
                with open(final_path, "wb+") as destination:
                    destination.write(file_content)
                print(f"[BIM] File written to disk successfully", flush=True)

            print(f"[BIM] Calculating relative path", flush=True)
            relative_path = os.path.relpath(final_path, settings.MEDIA_ROOT)
            print(f"[BIM] Relative path: {relative_path}", flush=True)

            bim_file.file_path = relative_path
            print(f"[BIM] About to update BIMFile model in database", flush=True)
            bim_file.save()
            
            print(f"[BIM] File saved successfully: {bim_file.id}", flush=True)
            
            return Response(
                {
                    "success": True,
                    "file_id": str(bim_file.id),
                    "filename": bim_file.original_filename,
                    "file_type": bim_file.file_type,
                    "message": "Файл успешно загружен",
                    "size": bim_file.size
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            import traceback
            print(f"[BIM ERROR] Не удалось загрузить файл: {str(e)}", flush=True)
            print(f"[BIM ERROR] Traceback:", flush=True)
            traceback.print_exc()
            # Удаляем запись из БД если что-то пошло не так
            if "bim_file" in locals():
                try:
                    print(f"[BIM] Attempting to delete BIMFile record", flush=True)
                    bim_file.delete()
                    print(f"[BIM] BIMFile record deleted", flush=True)
                except Exception as del_err:
                    print(f"[BIM ERROR] Error deleting BIMFile: {str(del_err)}", flush=True)
                    traceback.print_exc()

            return Response(
                {"error": f"Не удалось загрузить файл: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileListView(TaskView):
    """API для получения списка файлов пользователя"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        files = BIMFile.objects.filter(user=request.user)

        file_list = []
        for f in files:
            file_list.append(
                {
                    "id": str(f.id),
                    "filename": f.original_filename,
                    "file_type": f.file_type,
                    "size": f.size,
                }
            )

        return Response({"files": file_list, "count": len(file_list)})


class FileDetailView(TaskView):
    """API для работы с конкретным файлом"""
    permission_classes = (IsAuthenticated,)

    def get(self, request, file_id):
        try:
            bim_file = BIMFile.objects.get(id=file_id, user=request.user)

            file_path = bim_file.get_absolute_path()
            if bim_file.file_type in ["LAZ", "LAS"]:
                metadata = get_pointcloud_info(file_path)
            elif bim_file.file_type == "GEOTIFF":
                metadata = get_geotiff_info(file_path)
            else:
                metadata = {}

            return Response(
                {
                    "id": str(bim_file.id),
                    "filename": bim_file.original_filename,
                    "file_type": bim_file.file_type,
                    "size": bim_file.size,
                    "metadata": metadata,
                    "file_path": bim_file.file_path,
                }
            )

        except BIMFile.DoesNotExist:
            return Response(
                {"error": "Файл не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to get file info: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, file_id):
        """Удалить файл"""
        try:
            bim_file = BIMFile.objects.get(id=file_id, user=request.user)
            filename = bim_file.original_filename
            bim_file.delete()

            return Response(
                {"success": True, "message": f"File {filename} deleted successfully"}
            )

        except BIMFile.DoesNotExist:
            return Response(
                {"error": "Файл не найден"}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": f"Не удалось удалить файл: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
