import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.agent import Agent
from app.tasks.workflow_tasks import execute_workflow

logger = logging.getLogger(__name__)


class SchedulerService:
    _task: asyncio.Task | None = None
    _running: bool = False

    @staticmethod
    async def start_scheduler():
        """Starts the periodic background scheduler task."""
        if SchedulerService._running:
            return

        SchedulerService._running = True
        SchedulerService._task = asyncio.create_task(SchedulerService._loop())
        logger.info("Background scheduler service started.")

    @staticmethod
    async def stop_scheduler():
        """Stops the periodic background scheduler task."""
        SchedulerService._running = False
        if SchedulerService._task:
            SchedulerService._task.cancel()
            try:
                await SchedulerService._task
            except asyncio.CancelledError:
                pass
        logger.info("Background scheduler service stopped.")

    @staticmethod
    async def _loop():
        # Wait 10 seconds initially for database and migrations to settle
        await asyncio.sleep(10)

        while SchedulerService._running:
            try:
                db: Session = SessionLocal()
                try:
                    # Query all active agents
                    agents = db.query(Agent).filter(Agent.active == True).all()

                    for agent in agents:
                        config = agent.schedule_config or {}
                        if not config.get("enabled", False):
                            continue

                        interval_minutes = float(config.get("interval_minutes", 0))
                        workflow_id = config.get("workflow_id")

                        if interval_minutes <= 0 or not workflow_id:
                            continue

                        # Check if it is time to run
                        last_run_str = config.get("last_run_at")
                        should_run = False
                        now = datetime.utcnow()

                        if not last_run_str:
                            should_run = True
                        else:
                            try:
                                last_run = datetime.fromisoformat(last_run_str)
                                elapsed_seconds = (now - last_run).total_seconds()
                                if elapsed_seconds >= (interval_minutes * 60):
                                    should_run = True
                            except ValueError:
                                should_run = True

                        if should_run:
                            logger.info(
                                f"Triggering scheduled run for agent '{agent.name}' "
                                f"on workflow ID {workflow_id} (Interval: {interval_minutes}m)"
                            )

                            # Dispatch asynchronous workflow run via Celery or fallback thread
                            prompt = f"Scheduled task executed by {agent.name} ({agent.role})"
                            
                            redis_available = False
                            try:
                                from app.runtime.memory_manager import memory
                                redis_available = memory._available
                            except Exception:
                                pass
                            
                            if redis_available:
                                try:
                                    execute_workflow.delay(workflow_id, prompt)
                                except Exception:
                                    redis_available = False
                            
                            if not redis_available:
                                from app.tasks.workflow_tasks import execute_workflow as execute_local
                                asyncio.create_task(asyncio.to_thread(execute_local, workflow_id, prompt))

                            # Update last_run_at timestamp
                            new_config = dict(config)
                            new_config["last_run_at"] = now.isoformat()
                            agent.schedule_config = new_config

                            db.commit()

                finally:
                    db.close()

            except Exception as e:
                logger.error(f"Error in scheduler background loop: {e}", exc_info=True)

            # Poll every 10 seconds for rapid testing responsiveness
            await asyncio.sleep(10)
