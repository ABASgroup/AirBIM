from base import BaseCRUD
from models.company import Company


class CompanyCRUD(BaseCRUD[Company]):
    """DAO class for CRUD operations with Company model."""
    _model = Company
