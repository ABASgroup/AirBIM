from celery import Celery
from celery.schedules import crontab
from kombu import Queue
from core.configs.celery import celery_config
from dependencies import get_storage, get_db_session


celery_app = Celery(
    celery_config.NAME,
    broker=celery_config.broker_url,
    backend=celery_config.backend_url,
    task_serializer=celery_config.SERIALIZER,
    result_serializer=celery_config.SERIALIZER,
    accept_content=[celery_config.SERIALIZER],
    timezone=celery_config.TIMEZONE,
    result_expires=celery_config.RESULT_EXPIRES
)

# register task queues
celery_app.conf.task_queues = (
    Queue("default"),
    Queue("heavy"),
    Queue("converter"),
)

celery_app.autodiscover_tasks(["tasks"])
