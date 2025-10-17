import logging

from app.models import Theme
from webodm import settings
from django.templatetags.static import static

logger = logging.getLogger("app.logger")


# Make the SETTINGS object available to all templates
def load(request=None):
    return {
        "SETTINGS": {
            "app_name": settings.APP_NAME,
            "app_logo": static(settings.APP_DEFAULT_LOGO),
            "app_logo_36": static(settings.APP_DEFAULT_LOGO_36),
            "app_logo_favicon": static(settings.APP_DEFAULT_LOGO_FAVICON),
            "organization_name": settings.ORGANIZATION_NAME,
            "organization_website": settings.ORGANIZATION_WEBSITE,
            "theme": Theme.objects.get(id=settings.DEFAULT_THEME_ID),
        }
    }
