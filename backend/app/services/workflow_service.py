from sqlalchemy.orm import Session

from app.models.workflow import Workflow


class WorkflowService:

    @staticmethod
    def create_workflow(db: Session, payload) -> Workflow:
        workflow = Workflow(
            name=payload.name,
            description=payload.description,
            graph=payload.graph,
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def get_workflows(db: Session) -> list[Workflow]:
        return db.query(Workflow).filter(Workflow.active == True).all()

    @staticmethod
    def get_workflow_by_id(db: Session, workflow_id: int) -> Workflow | None:
        return db.query(Workflow).filter(Workflow.id == workflow_id).first()

    @staticmethod
    def update_workflow(db: Session, workflow_id: int, payload) -> Workflow | None:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return None
        workflow.name = payload.name
        workflow.description = payload.description
        workflow.graph = payload.graph
        db.commit()
        db.refresh(workflow)
        return workflow

    @staticmethod
    def delete_workflow(db: Session, workflow_id: int) -> bool:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return False
        workflow.active = False
        db.commit()
        return True