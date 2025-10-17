import os
import time
import inspect

from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import Client

from app.contexts.settings import load as load_settings
from webodm import settings as webodm_settings
from .classes import BootTestCase

class TestSettings(BootTestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_settings(self):
        c = Client()

        # There should always be a settings file
        settings_file = inspect.getfile(webodm_settings)
        self.assertTrue(os.path.exists(settings_file), "webodm_settings file is accessible")

        # We can retrieve the settings
        settings = load_settings()['SETTINGS']
        self.assertTrue(settings is not None, "Can retrieve settings")

        # TODO: remove images from contexts/settings.py
        # The logos have been created in the proper destination
        self.assertTrue(settings["app_logo"], "Default logo exists")
        self.assertTrue(settings["app_logo_36"], "Default logo exists")
        self.assertTrue(settings["app_logo_favicon"], "Default logo exists")
