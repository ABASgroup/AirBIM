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
    """API for uploading LAS/LAZ and GeoTIFF files"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if "file" not in request.FILES:
            return Response(
                {"error": _("File was not provided")}, status=status.HTTP_400_BAD_REQUEST
            )

        uploaded_file = request.FILES["file"]

        if not validate_file_type(uploaded_file, [".las", ".laz", ".tif", ".tiff"]):
            return Response(
                {"error": _("Unsupported file type. Allowed: LAZ, LAS or GeoTIFF")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extension = uploaded_file.name.split(".")[-1].upper()
        if extension in ["TIF", "TIFF"]:
            file_type = "GEOTIFF"
        else:
            file_type = extension

        # Read the file content from the temporary path (file is already closed by custom upload handler)
        try:
            # Check if temporary_file_path method exists (for closed temporary files)
            if hasattr(uploaded_file, 'temporary_file_path'):
                temp_file_path = uploaded_file.temporary_file_path()
                with open(temp_file_path, 'rb') as f:
                    file_content = f.read()
            else:
                # For in-memory files
                file_content = uploaded_file.read()
            
        except Exception as e:
            return Response(
                {"error": _("Failed to read file: %s") % str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # First create a DB record without saving to get the ID
            bim_file = BIMFile(
                user=request.user,
                file_type=file_type,
                original_filename=uploaded_file.name,
                size=uploaded_file.size,
            )
            # First save to get ID
            bim_file.save()

            # Form the path: MEDIA_ROOT/bim/user_<id>/<type>/<file_id>/
            file_dir = os.path.join(
                settings.MEDIA_ROOT,
                "bim",
                f"user_{request.user.id}",
                file_type.lower(),
                str(bim_file.id),
            )
            os.makedirs(file_dir, exist_ok=True)

            # If the file is LAS, convert it to LAZ
            if file_type == "LAS":
                temp_las_path = os.path.join(file_dir, "temp.las")
                with open(temp_las_path, "wb+") as destination:
                    destination.write(file_content)
                
                final_filename = os.path.splitext(uploaded_file.name)[0] + ".laz"
                final_path = os.path.join(file_dir, final_filename)
                convert_las_to_laz(temp_las_path, final_path)
                os.remove(temp_las_path)
            else:
                final_filename = uploaded_file.name
                final_path = os.path.join(file_dir, final_filename)
                
                # Write the file content that we read earlier
                with open(final_path, "wb+") as destination:
                    destination.write(file_content)

            relative_path = os.path.relpath(final_path, settings.MEDIA_ROOT)

            bim_file.file_path = relative_path
            bim_file.save()
            
            return Response(
                {
                    "success": True,
                    "file_id": str(bim_file.id),
                    "filename": bim_file.original_filename,
                    "file_type": bim_file.file_type,
                    "message": _("File uploaded successfully"),
                    "size": bim_file.size
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            # Delete the DB record if something went wrong
            if "bim_file" in locals():
                try:
                    bim_file.delete()
                except Exception as del_err:
                    pass

            return Response(
                {"error": _("Failed to upload file: %s") % str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class FileListView(TaskView):
    """API for getting the list of user's files"""
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
    """API for working with a specific file"""
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
                {"error": _("File not found")}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": _("Failed to get file info: %s") % str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, file_id):
        """Delete file"""
        try:
            bim_file = BIMFile.objects.get(id=file_id, user=request.user)
            filename = bim_file.original_filename
            bim_file.delete()

            return Response(
                {"success": True, "message": _("File %s deleted successfully") % filename}
            )

        except BIMFile.DoesNotExist:
            return Response(
                {"error": _("File not found")}, status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"error": _("Failed to delete file: %s") % str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
