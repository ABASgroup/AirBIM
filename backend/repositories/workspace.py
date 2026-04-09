from .base import BaseRepository
from models.workspace import Workspace


class WorkspaceRepository(BaseRepository[Workspace]):
    """Repository class for CRUD operations with Workspace model."""
    _model = Workspace
