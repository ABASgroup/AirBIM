from .base import BaseCRUD
from models.workspace import Workspace


class WorkspaceCRUD(BaseCRUD[Workspace]):
    """DAO class for CRUD operations with Workspace model."""
    _model = Workspace
