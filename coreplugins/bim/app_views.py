import json
import requests

from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def HomeView(plugin):
    @login_required
    def view(request):
        # Определяем базовый URL в зависимости от того, как зашли
        api_upload_url = "/api" + plugin.public_url("upload")
        api_files_url = "/api" + plugin.public_url("files")
        api_files_2_url = "/api" + plugin.public_url("files/")
        
        return render(
            request,
            plugin.template_path("app.html"),
            {
                "title": "Test", 
                "plugin": plugin,
                "test_url": "/bim/test",
                "api_upload_url": api_upload_url,
                "api_files_url": api_files_url,
                "api_files_2_url": api_files_2_url,
            },
        )

    return view

def TestView(plugin):
    @login_required
    def view(request):
        
        return render(
            request,
            plugin.template_path("test.html"),
            {
                "title": "Test", 
                "plugin": plugin,
                "home_url": "/bim"
            },
        )

    return view