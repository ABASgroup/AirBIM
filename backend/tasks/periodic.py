import asyncio
from infrastructure.celery_app import celery_app, Celery
from celery.schedules import crontab
from celery import shared_task
from services.file import FileService
from core.dependencies import get_database_uow


class PeriodicTask(celery_app.Task):
    queue = 'default'


@celery_app.task(base=PeriodicTask, ignore_result=True)
def clean_up_files():
    """Cleans up files from the storage and the database periodically."""


@celery_app.task(base=PeriodicTask,  ignore_result=True)
def test():
    print(f'HELLO WORLD')
