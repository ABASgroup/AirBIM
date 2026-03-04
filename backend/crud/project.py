from .base import BaseCRUD
from models.project import Project


class ProjectCRUD(BaseCRUD[Project]):
    """DAO class for CRUD operations with Project model."""
    _model = Project
