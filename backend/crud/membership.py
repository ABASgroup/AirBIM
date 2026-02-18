from base import BaseCRUD
from models.membership import Membership


class MembershipCRUD(BaseCRUD[Membership]):
    """DAO class for CRUD operations with Membership model."""
    _model = Membership
