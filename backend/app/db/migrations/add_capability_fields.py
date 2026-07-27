import logging
from sqlalchemy import inspect, text
from app.db.database import Base, engine
from app.models.workflow_failure_policy import WorkflowFailurePolicy

logger = logging.getLogger(__name__)

def run_migrations():
    """
    Safely adds capability classification columns and new policy tables
    if they do not already exist.
    """
    try:
        # Create any missing tables (e.g. workflow_failure_policies)
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        
        # 1. Check mcp_servers table
        if inspector.has_table("mcp_servers"):
            columns = [c["name"] for c in inspector.get_columns("mcp_servers")]
            with engine.begin() as conn:
                if "category" not in columns:
                    logger.info("Migrating mcp_servers: adding category column")
                    conn.execute(text("ALTER TABLE mcp_servers ADD COLUMN category VARCHAR DEFAULT 'YUNO_TOOLS'"))

        # 2. Check mcp_tools table
        if inspector.has_table("mcp_tools"):
            columns = [c["name"] for c in inspector.get_columns("mcp_tools")]
            with engine.begin() as conn:
                if "exposure" not in columns:
                    logger.info("Migrating mcp_tools: adding exposure column")
                    conn.execute(text("ALTER TABLE mcp_tools ADD COLUMN exposure VARCHAR DEFAULT 'BUILDER_VISIBLE'"))
                if "risk_level" not in columns:
                    logger.info("Migrating mcp_tools: adding risk_level column")
                    conn.execute(text("ALTER TABLE mcp_tools ADD COLUMN risk_level VARCHAR DEFAULT 'LOW'"))
                if "requires_approval" not in columns:
                    logger.info("Migrating mcp_tools: adding requires_approval column")
                    conn.execute(text("ALTER TABLE mcp_tools ADD COLUMN requires_approval BOOLEAN DEFAULT FALSE"))

        logger.info("Capability classification DB migrations completed successfully.")
    except Exception as e:
        logger.error(f"Error running DB migrations: {e}")

if __name__ == "__main__":
    run_migrations()
