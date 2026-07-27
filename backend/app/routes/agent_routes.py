from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.agent_schema import AgentCreate, AgentResponse, AgentUpdate
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/", response_model=list[AgentResponse])
def get_agents(db: Session = Depends(get_db)):
    return AgentService.get_agents(db)


@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    agent = AgentService.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("/", response_model=AgentResponse, status_code=201)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    return AgentService.create_agent(db, payload)


@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)):
    agent = AgentService.update_agent(db, agent_id, payload)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    deleted = AgentService.delete_agent(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")


@router.get("/{agent_id}/mcp-tools")
def get_agent_mcp_tools(agent_id: int, db: Session = Depends(get_db)):
    """Returns MCP tools assigned and authorized for this specific agent."""
    from app.models.mcp_server import AgentMCPTool, MCPTool
    assignments = (
        db.query(AgentMCPTool)
        .filter(AgentMCPTool.agent_id == agent_id, AgentMCPTool.enabled == True)
        .all()
    )
    results = []
    for a in assignments:
        if a.mcp_tool:
            t = a.mcp_tool
            results.append({
                "id": t.id,
                "canonical_name": f"mcp::{t.server.name}::{t.name}",
                "server_name": t.server.name,
                "tool_name": t.name,
                "description": t.description,
                "risk_level": t.risk_level,
                "requires_approval": t.requires_approval,
            })
    return results


@router.post("/{agent_id}/mcp-tools")
def assign_agent_mcp_tools(agent_id: int, payload: dict, db: Session = Depends(get_db)):
    """Assigns AGENT_ASSIGNABLE MCP tools to an Agent."""
    from app.models.agent import Agent
    from app.models.mcp_server import AgentMCPTool, MCPTool

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    mcp_tool_ids = payload.get("mcp_tool_ids", [])
    db.query(AgentMCPTool).filter(AgentMCPTool.agent_id == agent_id).delete()

    assigned = []
    for tool_id in mcp_tool_ids:
        tool = db.query(MCPTool).filter(MCPTool.id == tool_id, MCPTool.exposure == "AGENT_ASSIGNABLE").first()
        if tool:
            assign = AgentMCPTool(agent_id=agent_id, mcp_tool_id=tool_id, enabled=True)
            db.add(assign)
            assigned.append(assign)

    db.commit()
    return {
        "status": "success",
        "agent_id": agent_id,
        "assigned_mcp_tool_ids": [a.mcp_tool_id for a in assigned]
    }