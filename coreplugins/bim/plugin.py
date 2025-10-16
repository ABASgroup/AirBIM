from rest_framework import status
from rest_framework.response import Response

from app.plugins import PluginBase, Menu, MountPoint, get_current_plugin
from app.plugins.views import TaskView
from django.shortcuts import render
from django import forms

from .app_views import HomeView, TestView
from .api_views import UploadFileView, FileListView, FileDetailView

class Plugin(PluginBase):

    def main_menu(self):
        return [Menu("Test", "/bim/", "")]

    def root_mount_points(self):
        return [
            MountPoint('bim/$', HomeView(self)),
            MountPoint('bim/test$', TestView(self)),
        ]

    # def app_mount_points(self):
    #     return [
    #         MountPoint('$', HomeView(self)),
    #         MountPoint('test$', TestView(self)),
    #     ]

    def api_mount_points(self):
        return [
            MountPoint('upload$', UploadFileView.as_view()),
            MountPoint('files$', FileListView.as_view()),
            MountPoint('files/(?P<file_id>[^/.]+)$', FileDetailView.as_view()),
        ]
