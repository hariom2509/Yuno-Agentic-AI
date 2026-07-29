from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.execution import Execution

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("/")
def get_executions(db: Session = Depends(get_db)):
    executions = (
        db.query(Execution)
        .order_by(Execution.started_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": e.id,
            "workflow_id": e.workflow_id,
            "status": e.status,
            "current_node": e.current_node,
            "input_task": e.input_task,
            "final_output": e.final_output,
            "tokens_used": e.tokens_used,
            "cost_usd": e.cost_usd,
            "started_at": e.started_at.isoformat() if e.started_at else None,
            "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        }
        for e in executions
    ]


@router.get("/{execution_id}")
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    e = db.query(Execution).filter(Execution.id == execution_id).first()
    if not e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Execution not found")
    return {
        "id": e.id,
        "workflow_id": e.workflow_id,
        "status": e.status,
        "current_node": e.current_node,
        "input_task": e.input_task,
        "final_output": e.final_output,
        "tokens_used": e.tokens_used,
        "cost_usd": e.cost_usd,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
    }