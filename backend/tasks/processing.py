import asyncio
import uuid
from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.workspace import get_workspace
from core.dependencies import get_database_uow


# heavy tasks with long duration must never use database transaction for far too long
# use short transactions
# save artifacts

class ProcessingTask(celery_app.Task):
    queue = 'heavy'


@celery_app.task()
def test_celery():
    async def run_task():
        await asyncio.sleep(5)
        uow = get_database_uow()
        async with uow:
            workspace = await get_workspace(
                uuid.UUID("52612693-7492-4d91-9ce7-ce1cf3c9aaa7"), session=uow.session)
            print(workspace)

    run_async(run_task())
