import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OPENAI_API_KEY"] = "test"

from app.main import app
from app.db.database import Base, get_db

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.execution import Execution
from app.models.message import Message

from sqlalchemy.pool import StaticPool

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client that uses the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock the OpenAI service to avoid actual API calls during tests."""
    def mock_chat(*args, **kwargs):
        return {
            "content": "Mocked AI response",
            "tokens_in": 10,
            "tokens_out": 20,
            "total_tokens": 30,
            "cost_usd": 0.0001,
        }
    monkeypatch.setattr("app.services.openai_service.OpenAIService.chat", mock_chat)
    return mock_chat
