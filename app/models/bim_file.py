import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class BIMFile(models.Model):
    """
    Model for storing uploaded LAS/LAZ and GeoTIFF files (BIM plugin)
    """

    FILE_TYPE_CHOICES = [
        ("LAZ", "Point Cloud (LAZ)"),
        ("LAS", "Point Cloud (LAS)"),
        ("GEOTIFF", "GeoTIFF Raster"),
    ]

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text=_("User who uploaded this file"),
        verbose_name=_("User"),
    )

    file_type = models.CharField(
        max_length=10,
        choices=FILE_TYPE_CHOICES,
        help_text=_("Type of the file"),
        verbose_name=_("File Type"),
    )

    original_filename = models.CharField(
        max_length=255,
        help_text=_("Original filename"),
        verbose_name=_("Original Filename"),
    )

    file_path = models.CharField(
        max_length=512,
        help_text=_("Relative path to the file from MEDIA_ROOT"),
        verbose_name=_("File Path"),
    )

    size = models.BigIntegerField(
        help_text=_("File size in bytes"), verbose_name=_("Size")
    )

    class Meta:
        verbose_name = _("BIM File")
        verbose_name_plural = _("BIM Files")

    def __str__(self):
        return f"{self.original_filename} ({self.file_type})"

    def get_absolute_path(self):
        """Returns the absolute path to the file"""
        return os.path.join(settings.MEDIA_ROOT, self.file_path)

    def delete_file(self):
        """Deletes the file from the file system"""
        if not self.file_path:
            return

        file_path = self.get_absolute_path()
        if not file_path:
            return

        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass

            dir_path = os.path.dirname(file_path)
            bim_root = os.path.join(settings.MEDIA_ROOT, "bim")
            try:
                while (
                    dir_path and dir_path.startswith(bim_root) and dir_path != bim_root
                ):
                    if os.path.isdir(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        dir_path = os.path.dirname(dir_path)
                    else:
                        break
            except OSError:
                pass

    def delete(self, *args, **kwargs):
        """Override the delete method to remove the file"""
        self.delete_file()
        super().delete(*args, **kwargs)
