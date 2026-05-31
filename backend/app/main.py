import asyncio
import logging
import time
from dotenv import load_dotenv

# Load environment variables from all possible local paths
load_dotenv()
load_dotenv(".env")
load_dotenv("backend/.env")
load_dotenv("../.env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.db.database import engine, Base

# Import models to register them with SQLAlchemy
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.execution import Execution
from app.models.message import Message
from app.models.skill import Skill

from app.routes.agent_routes import router as agent_router
from app.routes.workflow_routes import router as workflow_router
from app.routes.execution_routes import router as execution_router
from app.routes.message_routes import router as message_router
from app.routes.monitoring_routes import router as monitoring_router
from app.routes.template_routes import router as template_router
from app.routes.skill_routes import router as skill_router

from app.websocket.manager import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger(__name__)


def wait_for_db():
    retries = 15
    while retries > 0:
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database connected and tables created.")
            return
        except OperationalError:
            retries -= 1
            logger.warning(f"Waiting for database... ({retries} retries left)")
            time.sleep(3)
    raise RuntimeError("Could not connect to database after 15 retries.")


wait_for_db()

app = FastAPI(
    title="Yuno AI Agent Orchestration Platform",
    description="Multi-agent workflow orchestration with LangGraph, Celery, and Telegram integration.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(workflow_router)
app.include_router(execution_router)
app.include_router(message_router)
app.include_router(monitoring_router)
app.include_router(template_router)
app.include_router(skill_router)


@app.websocket("/ws/executions")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Store loop reference so sync Celery workers can broadcast
    manager.set_loop(asyncio.get_event_loop())
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.on_event("startup")
async def startup():
    manager.set_loop(asyncio.get_event_loop())
    # Start Telegram bot in background
    from app.services.telegram_service import start_bot
    start_bot()
    # Start background scheduler
    from app.services.scheduler_service import SchedulerService
    await SchedulerService.start_scheduler()
    logger.info("Yuno AI Agent Platform started.")


@app.on_event("shutdown")
async def shutdown():
    from app.services.scheduler_service import SchedulerService
    await SchedulerService.stop_scheduler()
    logger.info("Yuno AI Agent Platform stopped.")


@app.get("/health")
def health_check():
    return {"status": "running", "version": "1.0.0"}


# SPA Single-Container Static Files Routing Fallback
import os
from fastapi.responses import FileResponse

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.exists(STATIC_DIR):
    from fastapi.staticfiles import StaticFiles
    
    # Mount `/static` sub-assets folder if compiled
    static_assets = os.path.join(STATIC_DIR, "static")
    if os.path.exists(static_assets):
        app.mount("/static", StaticFiles(directory=static_assets), name="static")
    
    # SPA catch-all endpoint: routes non-file hits back to index.html for React routing
    @app.get("/{catchall:path}")
    async def serve_spa(catchall: str):
        file_path = os.path.join(STATIC_DIR, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))