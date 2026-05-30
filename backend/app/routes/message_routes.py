from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.message import Message

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/")
def get_messages(execution_id: int = None, db: Session = Depends(get_db)):
    query = db.query(Message).order_by(Message.timestamp.asc())
    if execution_id:
        query = query.filter(Message.execution_id == execution_id)
    messages = query.limit(200).all()
    return [
        {
            "id": m.id,
            "execution_id": m.execution_id,
            "sender": m.sender,
            "receiver": m.receiver,
            "content": m.content,
            "message_type": m.message_type,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        }
        for m in messages
    ]