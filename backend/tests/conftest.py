"""Shared pytest fixtures for integration and API tests."""
from collections.abc import AsyncIterator
from pathlib import Path

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_storage
from infrastructure.database import session_maker
from infrastructure.storage import Storage
from main import app
from models import User, Membership, Workspace, Project, Stage, BIM, PointCloud, File, PointCloudConverted, InviteLink


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
TEST_BUILDING_IFC = FIXTURES_DIR / "TestBuilding.ifc"
TEST_BUILDING_LAZ = FIXTURES_DIR / "TestBuilding.laz"
TEST_BUILDING_SHIFTED_LAZ = FIXTURES_DIR / "TestBuildingShifted.laz"
TEST_PHOTO_1_JPG = FIXTURES_DIR / "TestPhoto1.jpg"
TEST_PHOTO_2_JPG = FIXTURES_DIR / "TestPhoto2.jpg"
TEST_PHOTO_3_PNG = FIXTURES_DIR / "TestPhoto3.png"
TEST_REPORT_PDF = FIXTURES_DIR / "TestReport.pdf"
TEST_REPORT_XLSX = FIXTURES_DIR / "TestReport.xlsx"


# ------------------------------ Fixture to create test data ------------------------------
def assert_existing_file(path: Path) -> Path:
    """Assert that the given path points to an existing, non-empty file."""
    assert path.is_file(), f"Missing test fixture: {path}"
    assert path.stat().st_size > 0, f"Empty test fixture: {path}"
    return path


@pytest.fixture(scope="session")
def test_building_ifc_path() -> Path:
    """Provide path to the test IFC file."""
    return assert_existing_file(TEST_BUILDING_IFC)


@pytest.fixture(scope="session")
def test_building_laz_path() -> Path:
    """Provide path to the test LAZ file."""
    return assert_existing_file(TEST_BUILDING_LAZ)


@pytest.fixture(scope="session")
def test_building_shifted_laz_path() -> Path:
    """Provide path to the test shifted LAZ file."""
    return assert_existing_file(TEST_BUILDING_SHIFTED_LAZ)


@pytest.fixture(scope="session")
def test_photo_1_jpg_path() -> Path:
    """Provide path to the first test photo."""
    return assert_existing_file(TEST_PHOTO_1_JPG)


@pytest.fixture(scope="session")
def test_photo_2_jpg_path() -> Path:
    """Provide path to the second test photo."""
    return assert_existing_file(TEST_PHOTO_2_JPG)


@pytest.fixture(scope="session")
def test_photo_3_png_path() -> Path:
    """Provide path to the third test photo."""
    return assert_existing_file(TEST_PHOTO_3_PNG)


@pytest.fixture(scope="session")
def test_report_pdf_path() -> Path:
    """Provide path to the test PDF report."""
    return assert_existing_file(TEST_REPORT_PDF)


@pytest.fixture(scope="session")
def test_report_xlsx_path() -> Path:
    """Provide path to the test XLSX report."""
    return assert_existing_file(TEST_REPORT_XLSX)
# ----------------------------------------------------------------------------------------------


# ------------------------------ Database and API client fixtures ------------------------------
async def _clean_database(session: AsyncSession) -> None:
    """Delete test data in child-to-parent order to satisfy foreign keys."""
    await session.rollback()
    await session.execute(delete(PointCloudConverted))
    await session.execute(delete(BIM))
    await session.execute(delete(PointCloud))
    await session.execute(delete(File))
    await session.execute(delete(Stage))
    await session.execute(delete(Project))
    await session.execute(delete(InviteLink))
    await session.execute(delete(Membership))
    await session.execute(delete(User))
    await session.execute(delete(Workspace))
    await session.commit()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncIterator[AsyncSession]:
    """Provide isolated database session for integration tests."""
    async with session_maker() as session:
        await _clean_database(session)
        try:
            yield session
        finally:
            await _clean_database(session)


@pytest_asyncio.fixture(scope="function")
async def api_client() -> AsyncIterator[AsyncClient]:
    """Provide API client and ensure database cleanup via db_session fixture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def storage() -> AsyncIterator[Storage]:
    """Provide storage instance for tests."""
    storage_instance = get_storage()
    try:
        yield storage_instance
    finally:
        # Clean up all files in the storage after each test
        bucket = storage_instance._resource.Bucket(
            storage_instance._bucket_name)
        keys_to_delete = [{"Key": obj.key} for obj in bucket.objects.all()]
        if keys_to_delete:
            for i in range(0, len(keys_to_delete), 1000):
                batch = keys_to_delete[i:i + 1000]
                storage_instance._client.delete_objects(
                    Bucket=storage_instance._bucket_name,
                    Delete={"Objects": batch}
                )
# ----------------------------------------------------------------------------------------------
