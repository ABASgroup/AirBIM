"""Celery configuration."""
from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from core.configs.celery import celery_config


# register tasks modules here
TASK_MODULES = ('tasks.processing', 'tasks.periodic')

# celery app main configuration
celery_app = Celery(
    celery_config.NAME,
    broker=celery_config.BROKER_URL,
    backend=celery_config.BACKEND_URL,
    task_serializer=celery_config.SERIALIZER,
    result_serializer=celery_config.SERIALIZER,
    accept_content=[celery_config.SERIALIZER],
    timezone=celery_config.TIMEZONE,
    result_expires=celery_config.RESULT_EXPIRES,
    task_default_queue='default',
    include=TASK_MODULES,
)

# register task queues
celery_app.conf.task_queues = (
    Queue("default"),
    Queue("heavy"),
    Queue("converter"),
)

# register periodic tasks schedule
# if you don't register task here - it would not be executed
celery_app.conf.beat_schedule = {
    'periodic-cleanup-every-midnight': {
        'task': 'tasks.periodic.clean_up_files',
        'schedule': crontab(hour=0, minute=0),
        'options': {'queue': 'default'}
    },
    'test-30-seconds': {
        'task': 'tasks.periodic.test',
        'schedule': 30,
        'options': {'queue': 'default'}
    },
}
