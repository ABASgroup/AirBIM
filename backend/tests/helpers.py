"""Helper functions for testing."""
from repositories.workspace import WorkspaceRepository
from repositories.project import ProjectRepository
from repositories.stage import StageRepository
from repositories.files import FileRepository, PointCloudRepository, BIMRepository
from repositories.user import UserRepository
from repositories.membership import MembershipRepository

from schemas.workspace import WorkspaceModel, WorkspaceType
from schemas.project import ProjectModel
from schemas.stage import StageModel
from schemas.file import FileModel, PointCloudModel, BIMModel
from schemas.user import UserModel
from schemas.membership import MembershipModel

from services.file import FileService


async def create_test_workspace(db_session, workspace_type=WorkspaceType.TEAM):
    """Create workspace required by files.workspace_id foreign key."""
    return await WorkspaceRepository.create(
        WorkspaceModel(name="Repository files workspace",
                       type=workspace_type).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_project(db_session, workspace_id):
    """Create project required by BIM.project_id foreign key."""
    return await ProjectRepository.create(
        ProjectModel(name="Repository files project",
                     description="Project for testing files repository",
                     workspace_id=workspace_id).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_stage(db_session, project_id):
    """Create stage required by File.stage_id foreign key."""
    return await StageRepository.create(
        StageModel(project_id=project_id).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_file(db_session, workspace_id, file_path):
    """Create file required by PointCloud.file_id foreign key."""
    return await FileRepository.create(
        FileModel(
            workspace_id=workspace_id,
            **FileService.collect_file_data(file_path),
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_point_cloud(db_session, file_id):
    """Create point cloud required by RecordingResult.point_cloud_id foreign key."""
    return await PointCloudRepository.create(
        PointCloudModel(file_id=file_id).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_bim(db_session, project_id, file_id):
    """Create bim required by RecordingResult.bim foreign key."""
    return await BIMRepository.create(
        BIMModel(project_id=project_id, file_id=file_id).model_dump(
            exclude_unset=True),
        session=db_session,
    )


async def create_test_user(db_session, email="test@test.com", username="testuser", password_hashed="hashed-password"):
    """Create a user for testing."""
    return await UserRepository.create(
        UserModel(
            email=email,
            username=username,
            password_hashed=password_hashed,
        ).model_dump(exclude_unset=True),
        session=db_session,
    )


async def create_test_membership(db_session, workspace_id, user_id, role):
    """Create a membership for testing."""
    return await MembershipRepository.create(
        MembershipModel(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role
        ).model_dump(exclude_unset=True),
        session=db_session,
    )
