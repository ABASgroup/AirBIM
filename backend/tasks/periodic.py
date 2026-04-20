import asyncio
from infrastructure.celery import celery_app
from celery.schedules import crontab
from services.file import FileService
from core.dependencies import get_database_uow


# register periodic tasks
celery_app.conf.beat_schedule = {
    'clear_storage_every_day': {
        'task': 'tasks.clean_up_storage',
        'schedule': crontab(hour=0, minute=0),
    },
}


@celery_app.task
def clean_up_files():
    """Cleans up files from the storage and the database periodically."""