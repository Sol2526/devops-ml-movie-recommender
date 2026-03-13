from collections.abc import Generator
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

# added the project root explicitly so imports like `from app...` work the same way no matter how the pytest is launched.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.models import MovieFeedback
from app.db.session import get_session
from app.main import app


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session() -> Generator[Session, None, None]:
    with Session(test_engine) as session:
        yield session


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    app.dependency_overrides[get_session] = get_test_session

    # Using here TestClient as a context manager. Making sure startup logic runs the same way it would during normal exe.
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()