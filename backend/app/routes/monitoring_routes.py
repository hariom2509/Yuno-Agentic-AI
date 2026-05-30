from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.models.execution import Execution
from app.models.message import Message

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/executions")
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


@router.get("/executions/{execution_id}/messages")
def get_execution_messages(execution_id: int, db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.execution_id == execution_id)
        .order_by(Message.timestamp.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "receiver": m.receiver,
            "content": m.content,
            "message_type": m.message_type,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in messages
    ]


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_executions = db.query(func.count(Execution.id)).scalar()
    completed = db.query(func.count(Execution.id)).filter(Execution.status == "completed").scalar()
    failed = db.query(func.count(Execution.id)).filter(Execution.status == "failed").scalar()
    total_tokens = db.query(func.sum(Execution.tokens_used)).scalar() or 0
    total_cost = db.query(func.sum(Execution.cost_usd)).scalar() or 0.0

    return {
        "total_executions": total_executions,
        "completed": completed,
        "failed": failed,
        "total_tokens": total_tokens,
        "total_cost_usd": round(float(total_cost), 4),
    }