from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.workflow_schema import WorkflowCreate
from app.services.workflow_service import WorkflowService
from app.tasks.workflow_tasks import execute_workflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/")
def get_workflows(db: Session = Depends(get_db)):
    return WorkflowService.get_workflows(db)


@router.get("/{workflow_id}")
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = WorkflowService.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.post("/", status_code=201)
def create_workflow(payload: WorkflowCreate, db: Session = Depends(get_db)):
    return WorkflowService.create_workflow(db, payload)


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: int,
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
):
    workflow = WorkflowService.update_workflow(db, workflow_id, payload)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=204)
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    deleted = WorkflowService.delete_workflow(db, workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.post("/{workflow_id}/execute")
def run_workflow(
    workflow_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    body: dict = Body(default={}),
):
    workflow = WorkflowService.get_workflow_by_id(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    input_task = body.get("input_task", "")
    
    # Check if Redis/Celery is active to prevent blocking socket timeouts
    redis_available = False
    try:
        from app.runtime.memory_manager import memory
        redis_available = memory._available
    except Exception:
        pass

    task_id = "local_background_task"
    if redis_available:
        try:
            task = execute_workflow.delay(workflow_id, input_task)
            task_id = task.id
        except Exception:
            redis_available = False

    if not redis_available:
        # Fallback instantly (zero timeout) to local FastAPI BackgroundTasks thread
        from app.tasks.workflow_tasks import execute_workflow as execute_local
        background_tasks.add_task(execute_local, workflow_id, input_task)

    return {"message": "Workflow execution started", "task_id": task_id}