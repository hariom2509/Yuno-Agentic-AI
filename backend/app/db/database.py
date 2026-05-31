import os
from dotenv import load_dotenv

# Load environment variables from all possible local paths
load_dotenv()
load_dotenv(".env")
load_dotenv("backend/.env")
load_dotenv("../.env")

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

def test_connection(url: str) -> bool:
    try:
        # Use a short timeout of 2 seconds for verification to avoid blocking startup
        engine_check = create_engine(url, connect_args={"connect_timeout": 2} if not url.startswith("sqlite") else {})
        with engine_check.connect() as conn:
            pass
        return True
    except Exception:
        return False

# Robust fallback selection:
if DATABASE_URL:
    # If the provided URL connects successfully (e.g. Postgres container inside docker-compose), use it!
    if test_connection(DATABASE_URL):
        pass
    else:
        # Fallback 1: check for local postgres on localhost
        local_postgres = "postgresql://postgres:postgres@localhost:5432/yuno_ai"
        if test_connection(local_postgres):
            DATABASE_URL = local_postgres
        else:
            # Fallback 2: sqlite
            DATABASE_URL = "sqlite:///./yuno_ai.db"
else:
    DATABASE_URL = "sqlite:///./yuno_ai.db"

# SQLite requires different arguments for multi-threading safety
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()