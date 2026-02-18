from base import BaseCRUD
from models.user import User


class UserCRUD(BaseCRUD[User]):
    """DAO class for CRUD operations with User model."""
    _model = User
