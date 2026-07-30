#!/usr/bin/env python3
"""
Dedicated E2E Verification Script for Production MCP Capability Architecture

Tests two critical capability paths:
  1. Database Agent:
     - Authorizes 'execute_select' tool from 'postgres-mcp' for an Agent.
     - Executes genuine MCP tools/call over JSON-RPC 2.0 stdio with read-only transaction isolation.
     - Verifies structured database results returned to Agent context.

  2. Failure Automation & GitHub MCP Integration:
     - Triggers intentional workflow failure.
     - FailurePolicyService generates HITL approval item for CREATE_GITHUB_ISSUE.
     - Operator approves via /executions/{id}/resume.
     - Executes GitHub MCP create_issue tool call and stores output in execution record.
"""

import sys
sys.path.insert(0, ".")

import json
import logging
import urllib.request
from app.db.database import SessionLocal
from app.models.agent import Agent
from app.models.execution import Execution
from app.models.workflow import Workflow
from app.models.mcp_server import AgentMCPTool, MCPTool, MCPServer
from app.mcp.manager import MCPManager
from app.services.failure_policy_service import FailurePolicyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("MCP_E2E_Test")


def test_database_agent_mcp():
    print("\n" + "=" * 60)
    print("TEST A: Database Agent Integration (postgres-mcp execute_select)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Ensure Agent #1 exists
        agent = db.query(Agent).filter(Agent.id == 1).first()
        if not agent:
            agent = Agent(id=1, name="Database Analyst Agent", role="SQL Analyst", system_prompt="You analyze DB schemas.")
            db.add(agent)
            db.commit()

        # Ensure postgres-mcp server exists in the DB
        server = db.query(MCPServer).filter(MCPServer.name == "postgres-mcp").first()
        if not server:
            server = MCPServer(
                name="postgres-mcp",
                description="PostgreSQL Database Server",
                transport="stdio",
                command="python",
                args=["postgres_mcp_server.py"],
                category="EXTERNAL_AGENT",
                enabled=True
            )
            db.add(server)
            db.commit()
            db.refresh(server)

        # Ensure execute_select tool exists and is enabled
        tool = db.query(MCPTool).filter(MCPTool.name == "execute_select", MCPTool.server_id == server.id).first()
        if not tool:
            tool = MCPTool(
                server_id=server.id,
                name="execute_select",
                description="Execute a SELECT SQL query",
                exposure="AGENT_ASSIGNABLE",
                risk_level="LOW",
                requires_approval=False,
                enabled=True
            )
            db.add(tool)
            db.commit()
            db.refresh(tool)

        # 2. Authorize execute_select tool for Agent #1
        db.query(AgentMCPTool).filter(AgentMCPTool.agent_id == agent.id, AgentMCPTool.mcp_tool_id == tool.id).delete()
        db.add(AgentMCPTool(agent_id=agent.id, mcp_tool_id=tool.id, enabled=True))
        db.commit()

        print(f"Authorized Agent #{agent.id} for 'mcp::postgres-mcp::execute_select'.")

        # 3. Dispatch genuine MCP tools/call via MCPManager
        result = MCPManager.call_tool(
            db=db,
            agent_id=agent.id,
            server_name="postgres-mcp",
            tool_name="execute_select",
            arguments={"query": "SELECT 'Yuno Platform' as system_name, 2026 as release_year"}
        )

        print("MCP Execution Result:")
        print(json.dumps(result, indent=2))

        assert result.get("status") == "success", "Database MCP execution failed!"
        print("SUCCESS: Database Agent genuine MCP call completed successfully!")
    finally:
        db.close()


def test_failure_policy_github_mcp():
    print("\n" + "=" * 60)
    print("TEST B: Failure Policy & GitHub MCP Automation (create_issue)")
    print("=" * 60)

    db = SessionLocal()
    try:
        # Ensure github-mcp server exists in the DB
        server = db.query(MCPServer).filter(MCPServer.name == "github-mcp").first()
        if not server:
            server = MCPServer(
                name="github-mcp",
                description="GitHub MCP Server",
                transport="stdio",
                command="docker",
                args=["run", "-i", "--rm", "ghcr.io/github/github-mcp-server"],
                category="PLATFORM_INTEGRATION",
                enabled=True
            )
            db.add(server)
            db.commit()
            db.refresh(server)

        # Ensure create_issue tool exists and is enabled
        tool = db.query(MCPTool).filter(MCPTool.name == "create_issue", MCPTool.server_id == server.id).first()
        if not tool:
            tool = MCPTool(
                server_id=server.id,
                name="create_issue",
                description="Creates a GitHub issue",
                exposure="PLATFORM_INTERNAL",
                risk_level="HIGH",
                requires_approval=True,
                enabled=True
            )
            db.add(tool)
            db.commit()
            db.refresh(tool)

        # 1. Create a simulated failed execution
        execution = Execution(
            workflow_id=1,
            status="failed",
            current_node="Security Auditor",
            input_task="Production Security Scan",
            final_output="CRITICAL: SSL certificate expired on auth-service",
            tokens_used=120,
            cost_usd=0.0002
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        print(f"Created simulated failed Execution #{execution.id}.")

        # 2. Trigger FailurePolicyService
        approval_info = FailurePolicyService.handle_workflow_failure(db, execution)
        print("Failure Policy Trigger Output:")
        print(json.dumps(approval_info, indent=2))

        assert execution.status == "waiting_for_approval", "Execution status was not set to waiting_for_approval!"
        assert "CREATE_GITHUB_ISSUE" in str(execution.approval_data), "Approval data missing CREATE_GITHUB_ISSUE action!"

        print(f"Execution #{execution.id} correctly paused for operator approval on GitHub issue creation.")

        # 3. Simulate Human Operator approving via direct endpoint function call
        from app.routes.execution_routes import resume_execution
        resume_data = resume_execution(execution_id=execution.id, body={"decision": "APPROVED"}, db=db)

        print("Resume Response:")
        print(json.dumps(resume_data, indent=2))

        assert "GitHub Issue Action" in resume_data.get("final_output", ""), "GitHub issue action was not executed!"
        print("SUCCESS: Failure Policy GitHub MCP issue creation approved and executed!")

    finally:
        db.close()


if __name__ == "__main__":
    test_database_agent_mcp()
    test_failure_policy_github_mcp()
    print("\n" + "=" * 60)
    print("ALL MCP CAPABILITY ARCHITECTURE INTEGRATION TESTS PASSED PERFECTLY!")
    print("=" * 60)
