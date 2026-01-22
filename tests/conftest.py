from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.database import get_session
from src.main import app
from src.middleware.rate_limit import rate_limiter

# Import all models to ensure they are registered with SQLModel.metadata
# This MUST happen before create_all is called
from src.models import PasswordResetToken, RefreshToken, User  # noqa: F401


@pytest.fixture(name="engine", scope="function")
def engine_fixture() -> Generator[Engine, None, None]:
    # Use StaticPool to ensure SQLite in-memory DB persists across connections
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine


@pytest.fixture(name="session")
def session_fixture(engine: Engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine: Engine) -> Generator[TestClient, None, None]:
    def get_session_override() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    rate_limiter.reset()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
