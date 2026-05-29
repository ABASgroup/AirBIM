import uuid
from fastapi import APIRouter, Depends
from infrastructure.storage import Storage
from services import project as project_service
from services import stage as stage_service
from services.file import FileService
from schemas.project import ProjectResponse, ProjectUpdate
from schemas.stage import StageModel, StageResponse
from schemas.file import (
    FileDataRequest,
    FileLinkResponse,
    BIMResponse,
    FileModel,
    FileResponse
)
from core.roles import Permission
from core.dependencies import (
    get_database_uow,
    get_storage,
    DatabaseSessionUOW
)
from core.exceptions import NotFoundError
from tasks.processing import convert_bim_to_point_cloud
from api.dependencies import require_project_permission

router = APIRouter(prefix="/results", tags=["project results"])




