from .base import BaseCRUD
from backend.models.invite_link import InviteLink


class InviteLinkCRUD(BaseCRUD[InviteLink]):
    """DAO class for CRUD operations with InviteLink model."""
    _model = InviteLink
