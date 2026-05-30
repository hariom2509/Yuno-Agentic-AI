import logging

from app.tasks.celery_app import celery
from app.db.database import SessionLocal
from app.services.workflow_service import WorkflowService
from app.runtime.runtime_engine import RuntimeEngine

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=0)
def execute_workflow(self, workflow_id: int, input_task: str = ""):
    db = SessionLocal()
    try:
        workflow = WorkflowService.get_workflow_by_id(db, workflow_id)
        if not workflow:
            return {"error": f"Workflow {workflow_id} not found"}

        task_text = input_task or "Analyze OpenAI vs Anthropic enterprise positioning"
        execution = RuntimeEngine.execute_workflow(db, workflow, input_task=task_text)

        logger.info(f"Workflow {workflow_id} completed. Execution: {execution.id} | Status: {execution.status}")

        return {
            "execution_id": execution.id,
            "status": execution.status,
            "tokens": execution.tokens_used,
            "cost_usd": execution.cost_usd,
        }

    except Exception as e:
        logger.error(f"Workflow task {workflow_id} error: {e}")
        return {"error": str(e)}

    finally:
        db.close()