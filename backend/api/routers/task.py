from fastapi import APIRouter

router = APIRouter(
    prefix="/tasks/{task_id}",
    tags=["tasks"]
)
