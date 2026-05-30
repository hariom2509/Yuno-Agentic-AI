from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/templates", tags=["Templates"])

TEMPLATES = {
    "research_workflow": {
        "name": "Research & Analysis Workflow",
        "description": "A 3-agent pipeline: Researcher gathers data, Analyst extracts insights, Reporter structures the final output.",
        "graph": {
            "nodes": [
                {
                    "id": "researcher",
                    "type": "agentNode",
                    "position": {"x": 100, "y": 200},
                    "data": {
                        "label": "Research Agent",
                        "type": "agent",
                        "system_prompt": "You are a research specialist. Search and compile comprehensive information about the given topic.",
                        "model": "llama-3.3-70b-versatile",
                        "tool": "web_search",
                    },
                },
                {
                    "id": "analyst",
                    "type": "agentNode",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "Analysis Agent",
                        "type": "agent",
                        "system_prompt": "You are a senior business analyst. Analyze the research data, identify patterns, and extract strategic insights.",
                        "model": "llama-3.3-70b-versatile",
                    },
                },
                {
                    "id": "reporter",
                    "type": "agentNode",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "label": "Report Agent",
                        "type": "tool",
                        "tool": "report_generator",
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "researcher", "target": "analyst"},
                {"id": "e2", "source": "analyst", "target": "reporter"},
            ],
        },
    },
    "customer_support_workflow": {
        "name": "Customer Support Workflow",
        "description": "A 3-agent pipeline: Intake Agent classifies the query, Resolution Agent provides a solution, Escalation Agent handles complex cases.",
        "graph": {
            "nodes": [
                {
                    "id": "intake",
                    "type": "agentNode",
                    "position": {"x": 100, "y": 200},
                    "data": {
                        "label": "Intake Agent",
                        "type": "agent",
                        "system_prompt": "You are a customer support intake specialist. Classify the customer issue by type (billing, technical, general) and summarize the core problem clearly.",
                        "model": "llama-3.3-70b-versatile",
                    },
                },
                {
                    "id": "resolver",
                    "type": "agentNode",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "Resolution Agent",
                        "type": "agent",
                        "system_prompt": "You are an expert customer support resolver. Given a classified support issue, provide a detailed, empathetic resolution. Include step-by-step instructions when applicable.",
                        "model": "llama-3.3-70b-versatile",
                    },
                },
                {
                    "id": "reporter",
                    "type": "agentNode",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "label": "Summary Agent",
                        "type": "tool",
                        "tool": "report_generator",
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "intake", "target": "resolver"},
                {"id": "e2", "source": "resolver", "target": "reporter"},
            ],
        },
    },
    "content_moderation_workflow": {
        "name": "Content Moderation with Feedback Loop",
        "description": "A workflow with conditional routing. Generator writes content, Reviewer checks it. If 'reject' is found, it loops back to Generator. If 'approve', it publishes.",
        "graph": {
            "nodes": [
                {
                    "id": "generator",
                    "type": "agentNode",
                    "position": {"x": 100, "y": 200},
                    "data": {
                        "label": "Content Generator",
                        "type": "agent",
                        "system_prompt": "You are a content writer. Write a short, engaging paragraph about the given topic.",
                        "model": "llama-3.1-8b-instant",
                        "temperature": 0.9,
                    },
                },
                {
                    "id": "reviewer",
                    "type": "agentNode",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "label": "Quality Reviewer",
                        "type": "agent",
                        "system_prompt": "You are a quality reviewer. Review the content. If it is good, reply with exactly 'APPROVE'. If it needs work or lacks detail, reply with exactly 'REJECT' and provide feedback.",
                        "model": "llama-3.1-8b-instant",
                        "temperature": 0.1,
                    },
                },
                {
                    "id": "publisher",
                    "type": "agentNode",
                    "position": {"x": 700, "y": 200},
                    "data": {
                        "label": "Publisher Tool",
                        "type": "tool",
                        "tool": "report_generator",
                    },
                },
            ],
            "edges": [
                {"id": "e1", "source": "generator", "target": "reviewer"},
                {"id": "e2", "source": "reviewer", "target": "publisher", "data": {"condition": "approve"}},
                {"id": "e3", "source": "reviewer", "target": "generator", "data": {"condition": "reject"}, "animated": True},
            ],
        },
    },
}


@router.get("/")
def list_templates():
    return [
        {
            "id": key,
            "name": tpl["name"],
            "description": tpl["description"],
            "node_count": len(tpl["graph"]["nodes"]),
        }
        for key, tpl in TEMPLATES.items()
    ]


@router.post("/{template_id}/deploy")
def deploy_template(template_id: str, db: Session = Depends(get_db)):
    tpl = TEMPLATES.get(template_id)
    if not tpl:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Template not found")

    from app.schemas.workflow_schema import WorkflowCreate
    payload = WorkflowCreate(
        name=tpl["name"],
        description=tpl["description"],
        graph=tpl["graph"],
    )
    workflow = WorkflowService.create_workflow(db, payload)
    return {"message": "Workflow created from template", "workflow_id": workflow.id}