from infrastructure.celery_app import celery_app
from infrastructure.async_runtime import run_async
from services.file import FileService
from core.dependencies import get_database_uow, get_storage


class PeriodicTask(celery_app.Task):
    queue = 'default'


@celery_app.task(base=PeriodicTask, ignore_result=True)
def clean_up_files():
    """Cleans up files from the storage and the database periodically."""
    async def run_task():
        uow = get_database_uow()
        async with uow:
            files_deleted = await FileService.clean_up_files(
                storage=get_storage(),
                session=uow.session
            )
        return files_deleted
    files_deleted = run_async(run_task())
    # temporary no logger
    print(f"FILE CLEAN UP: FILES DELETED - {files_deleted}")


@celery_app.task(base=PeriodicTask,  ignore_result=True)
def test():
    print('HELLO WORLD')
