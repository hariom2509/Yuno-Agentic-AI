from sqlalchemy.orm import Session

from app.models.message import Message


class MessageDispatcher:

    @staticmethod
    def dispatch(
        db: Session,
        execution_id: int,
        sender: str,
        receiver: str,
        content: str
    ):

        message = Message(
            execution_id=execution_id,
            sender=sender,
            receiver=receiver,
            content=content
        )

        db.add(message)

        db.commit()

        db.refresh(message)

        return message