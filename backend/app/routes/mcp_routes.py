import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.agent import Agent
from app.models.mcp_server import AgentMCPTool, MCPTool, MCPServer
from app.schemas.mcp_schema import (
    AgentMCPToolAssign,
    MCPDiscoverResponse,
    MCPServerCreate,
    MCPServerResponse,
    MCPServerUpdate,
    MCPToolResponse,
    MCPToolUpdate,
)
from app.mcp.registry import MCPToolRegistry
from app.mcp.manager import MCPManager
from app.mcp.exceptions import MCPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp-servers", tags=["MCP Servers"])


@router.get("", response_model=List[MCPServerResponse])
def list_mcp_servers(db: Session = Depends(get_db)):
    """List all registered MCP servers and their cached tools."""
    servers = db.query(MCPServer).all()
    return servers


@router.get("/tools/all")
def get_all_mcp_tools(db: Session = Depends(get_db)):
    """Returns all discovered & cached MCP tools formatted for workflow routing."""
    mcp_tools = db.query(MCPTool).filter(MCPTool.enabled == True).all()
    results = []
    for t in mcp_tools:
        if t.server and t.server.enabled:
            results.append({
                "id": t.id,
                "formatted_name": f"mcp::{t.server.name}::{t.name}",
                "server_name": t.server.name,
                "tool_name": t.name,
                "description": t.description,
            })
    return results


@router.get("/tools/manage")
def list_all_tools_for_management(db: Session = Depends(get_db)):
    """List all MCP tools across all servers with exposure, risk level, approval requirement, and status."""
    tools = db.query(MCPTool).join(MCPServer).all()
    results = []
    for t in tools:
        results.append({
            "id": t.id,
            "server_id": t.server_id,
            "server_name": t.server.name if t.server else "unknown",
            "name": t.name,
            "formatted_name": f"mcp::{t.server.name}::{t.name}" if t.server else t.name,
            "description": t.description,
            "exposure": t.exposure,
            "risk_level": t.risk_level,
            "requires_approval": t.requires_approval,
            "enabled": t.enabled,
            "discovered_at": t.discovered_at.isoformat() if t.discovered_at else None,
        })
    return results


@router.put("/tools/{tool_id}")
def update_mcp_tool_configuration(tool_id: int, payload: MCPToolUpdate, db: Session = Depends(get_db)):
    """Admin configuration: Update an MCP tool's exposure tier, risk level, approval requirement, or enabled status."""
    tool = db.query(MCPTool).filter(MCPTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP Tool not found.")

    if payload.exposure is not None:
        if payload.exposure not in ("BUILDER_VISIBLE", "AGENT_ASSIGNABLE", "PLATFORM_INTERNAL"):
            raise HTTPException(status_code=400, detail="Invalid exposure tier")
        tool.exposure = payload.exposure
    if payload.risk_level is not None:
        if payload.risk_level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise HTTPException(status_code=400, detail="Invalid risk level")
        tool.risk_level = payload.risk_level
    if payload.requires_approval is not None:
        tool.requires_approval = payload.requires_approval
    if payload.enabled is not None:
        tool.enabled = payload.enabled

    db.commit()
    db.refresh(tool)
    return {
        "status": "success",
        "tool": {
            "id": tool.id,
            "name": tool.name,
            "exposure": tool.exposure,
            "risk_level": tool.risk_level,
            "requires_approval": tool.requires_approval,
            "enabled": tool.enabled,
        }
    }


@router.post("", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
def register_mcp_server(payload: MCPServerCreate, db: Session = Depends(get_db)):
    """Register a new MCP server."""
    existing = db.query(MCPServer).filter(MCPServer.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MCP server with name '{payload.name}' already exists.",
        )

    server = MCPServer(
        name=payload.name,
        description=payload.description,
        transport=payload.transport,
        command=payload.command,
        args=payload.args or [],
        url=payload.url,
        secret_reference=payload.secret_reference,
        env_vars=payload.env_vars or {},
        enabled=payload.enabled,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    return server


@router.get("/{server_id}", response_model=MCPServerResponse)
def get_mcp_server(server_id: int, db: Session = Depends(get_db)):
    """Get details of a specific MCP server."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found.")
    return server


@router.put("/{server_id}", response_model=MCPServerResponse)
def update_mcp_server(server_id: int, payload: MCPServerUpdate, db: Session = Depends(get_db)):
    """Update configuration of an existing MCP server."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found.")

    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(server, field, value)

    db.commit()
    db.refresh(server)
    MCPManager.clear_sessions()
    return server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mcp_server(server_id: int, db: Session = Depends(get_db)):
    """Delete an MCP server registration."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found.")

    db.delete(server)
    db.commit()
    MCPManager.clear_sessions()
    return None


@router.post("/{server_id}/refresh-tools", response_model=MCPDiscoverResponse)
def refresh_mcp_server_tools(server_id: int, db: Session = Depends(get_db)):
    """Trigger tool discovery on target server and update database cache."""
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    if not server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found.")

    try:
        discovered_tools = MCPToolRegistry.discover_and_cache_tools(db, server)
        tool_responses = [MCPToolResponse.from_orm(t) for t in discovered_tools]
        return MCPDiscoverResponse(
            server_id=server.id,
            server_name=server.name,
            tools_count=len(tool_responses),
            tools=tool_responses,
        )
    except MCPException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/agents/{agent_id}/mcp-tools", status_code=status.HTTP_200_OK)
def authorize_agent_mcp_tools(agent_id: int, payload: AgentMCPToolAssign, db: Session = Depends(get_db)):
    """Assign/authorize specific MCP tools for an Agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")

    # Remove existing assignments
    db.query(AgentMCPTool).filter(AgentMCPTool.agent_id == agent_id).delete()

    new_assignments = []
    for tool_id in payload.mcp_tool_ids:
        tool = db.query(MCPTool).filter(MCPTool.id == tool_id).first()
        if tool:
            assign = AgentMCPTool(agent_id=agent_id, mcp_tool_id=tool_id, enabled=True)
            db.add(assign)
            new_assignments.append(assign)

    db.commit()
    return {
        "status": "success",
        "agent_id": agent_id,
        "authorized_mcp_tool_ids": [a.mcp_tool_id for a in new_assignments],
    }


# -------------------------------------------------------------------------
# NEW: Register & Discover the Built-in Genuine MCP Server
# -------------------------------------------------------------------------

@router.post("/seed-all", status_code=status.HTTP_201_CREATED)
def seed_all_mcp_servers(db: Session = Depends(get_db)):
    """
    Seeds all 3 MCP Capability Servers into the platform with appropriate classification:
      1. Yuno Tools (YUNO_TOOLS -> BUILDER_VISIBLE)
      2. PostgreSQL MCP (EXTERNAL_AGENT -> AGENT_ASSIGNABLE)
      3. GitHub MCP (PLATFORM_INTEGRATION -> PLATFORM_INTERNAL)
    """
    import os
    from pathlib import Path

    mcp_servers_dir = Path(__file__).parent.parent / "mcp" / "servers"

    # 1. Seed Yuno Tools MCP Server
    yuno_script = str(mcp_servers_dir / "yuno_native_server.py")
    yuno_server = db.query(MCPServer).filter(MCPServer.name == "yuno-tools").first()
    if not yuno_server:
        # Check legacy name
        yuno_server = db.query(MCPServer).filter(MCPServer.name == "yuno-native-mcp").first()
    
    if yuno_server:
        yuno_server.name = "yuno-tools"
        yuno_server.command = "python"
        yuno_server.args = [yuno_script]
        yuno_server.category = "YUNO_TOOLS"
        yuno_server.enabled = True
    else:
        yuno_server = MCPServer(
            name="yuno-tools",
            description="Genuine MCP Server exposing Yuno workflow tools via JSON-RPC 2.0 stdio.",
            transport="stdio",
            command="python",
            args=[yuno_script],
            category="YUNO_TOOLS",
            enabled=True,
        )
        db.add(yuno_server)
    db.commit()
    db.refresh(yuno_server)

    try:
        discovered = MCPToolRegistry.discover_and_cache_tools(db, yuno_server)
        for t in discovered:
            t.exposure = "BUILDER_VISIBLE"
            t.risk_level = "LOW"
            t.requires_approval = False
        db.commit()
    except Exception as e:
        logger.warning(f"Discovery for yuno-tools failed: {e}")

    # 2. Seed PostgreSQL MCP Server
    pg_script = str(mcp_servers_dir / "postgres_mcp_server.py")
    pg_server = db.query(MCPServer).filter(MCPServer.name == "postgres-mcp").first()
    if pg_server:
        pg_server.command = "python"
        pg_server.args = [pg_script]
        pg_server.category = "EXTERNAL_AGENT"
        pg_server.enabled = True
    else:
        pg_server = MCPServer(
            name="postgres-mcp",
            description="Dual-connection PostgreSQL MCP Server with read-only and write transaction isolation.",
            transport="stdio",
            command="python",
            args=[pg_script],
            category="EXTERNAL_AGENT",
            enabled=True,
        )
        db.add(pg_server)
    db.commit()
    db.refresh(pg_server)

    try:
        discovered_pg = MCPToolRegistry.discover_and_cache_tools(db, pg_server)
        for t in discovered_pg:
            t.exposure = "AGENT_ASSIGNABLE"
            if t.name in ("truncate_table", "drop_table"):
                t.risk_level = "CRITICAL"
                t.requires_approval = True
            elif t.name in ("insert_row", "update_rows"):
                t.risk_level = "HIGH"
                t.requires_approval = True
            else:
                t.risk_level = "LOW"
                t.requires_approval = False
        db.commit()
    except Exception as e:
        logger.warning(f"Discovery for postgres-mcp failed: {e}")

    # 3. Seed GitHub MCP Server
    gh_server = db.query(MCPServer).filter(MCPServer.name == "github-mcp").first()
    if gh_server:
        gh_server.transport = "stdio"
        gh_server.command = "docker"
        gh_server.args = ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"]
        gh_server.secret_reference = "env:GITHUB_PERSONAL_ACCESS_TOKEN"
        gh_server.category = "PLATFORM_INTEGRATION"
        gh_server.enabled = True
    else:
        gh_server = MCPServer(
            name="github-mcp",
            description="Official GitHub MCP Server running via Docker stdio for platform issue automation.",
            transport="stdio",
            command="docker",
            args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
            secret_reference="env:GITHUB_PERSONAL_ACCESS_TOKEN",
            category="PLATFORM_INTEGRATION",
            enabled=True,
        )
        db.add(gh_server)
    db.commit()
    db.refresh(gh_server)

    # Seed default GitHub MCP platform tools manually in case Docker daemon is off at startup
    gh_tools = [
        ("create_issue", "Creates a GitHub issue on workflow failure.", "PLATFORM_INTERNAL", "HIGH", True),
        ("delete_repository", "Deletes a GitHub repository.", "PLATFORM_INTERNAL", "CRITICAL", True),
    ]
    for tool_name, desc, exp, risk, req_app in gh_tools:
        existing_t = db.query(MCPTool).filter(MCPTool.server_id == gh_server.id, MCPTool.name == tool_name).first()
        if not existing_t:
            db.add(MCPTool(
                server_id=gh_server.id,
                name=tool_name,
                description=desc,
                exposure=exp,
                risk_level=risk,
                requires_approval=req_app,
                enabled=True,
            ))
    db.commit()

    return {
        "status": "success",
        "message": "All 3 MCP capability servers seeded and classified successfully.",
        "servers": ["yuno-tools", "postgres-mcp", "github-mcp"]
    }

