from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

class ConverterTask(celery_app.Task):
    queue = 'converter'


@celery_app.task()
def test_celery():
    async def run_task():
        pass
    run_async(run_task())