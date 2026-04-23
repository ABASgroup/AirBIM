"""Celery configuration."""
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from kombu import Queue
from core.configs.celery import celery_config
from infrastructure.async_runtime import init_worker_event_loop, close_worker_event_loop


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
        'schedule': 60,
        'options': {'queue': 'default'}
    },
    'test-30-seconds': {
        'task': 'tasks.periodic.test',
        'schedule': 30,
        'options': {'queue': 'default'}
    },
}

# on each worker process we should create a
# separate async loop to avoid troubles with
# concurrency for the database connection


@worker_process_init.connect
def _init_async_runtime(**_kwargs):
    init_worker_event_loop()


@worker_process_shutdown.connect
def _shutdown_async_runtime(**_kwargs):
    close_worker_event_loop()
