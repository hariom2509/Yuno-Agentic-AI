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

# If running locally outside docker and Postgres is not started, fallback to SQLite
if not DATABASE_URL or "@postgres:" in DATABASE_URL:
    try:
        # Check if a local postgres is running on localhost
        temp_url = "postgresql://postgres:postgres@localhost:5432/yuno_ai"
        engine_check = create_engine(temp_url)
        with engine_check.connect() as conn:
            pass
        DATABASE_URL = temp_url
    except Exception:
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