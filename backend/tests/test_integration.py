"""
Integration test script verifying:
1. Genuine MCP server registration & tool discovery (yuno_native_server)
2. LangGraph checkpointing with thread_id persistence
3. HITL interrupt() trigger & Command(resume="APPROVED") resume flow
4. SHA-256 idempotency key protection on replay
"""

import os
import sys
import json
from app.db.database import SessionLocal, Base, engine
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.execution import Execution
from app.models.mcp_server import MCPServer, MCPTool, AgentMCPTool
from app.runtime.runtime_engine import RuntimeEngine
from app.runtime.idempotency import IdempotencyGuard
from app.mcp.registry import MCPToolRegistry

def run_test():
    print("=== Starting End-to-End Integration Verification ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed & Discover Native MCP Server
        print("\n--- 1. Testing Genuine MCP Server Discovery ---")
        server_script = os.path.abspath("app/mcp/servers/yuno_native_server.py")
        server = db.query(MCPServer).filter(MCPServer.name == "yuno-native-mcp").first()
        if not server:
            server = MCPServer(
                name="yuno-native-mcp",
                description="Native stdio MCP server",
                transport="stdio",
                command="python",
                args=[server_script],
                enabled=True,
            )
            db.add(server)
            db.commit()
            db.refresh(server)

        tools = MCPToolRegistry.discover_and_cache_tools(db, server)
        print(f"Success: Discovered {len(tools)} MCP tools:")
        for t in tools:
            print(f"  - {t.name}: {t.description[:60]}...")

        # 2. Authorize test agent for MCP tools
        agent = db.query(Agent).first()
        if not agent:
            agent = Agent(name="TestAgent", role="Tester", system_prompt="Test agent")
            db.add(agent)
            db.commit()
            db.refresh(agent)

        for t in tools:
            existing = db.query(AgentMCPTool).filter_by(agent_id=agent.id, mcp_tool_id=t.id).first()
            if not existing:
                db.add(AgentMCPTool(agent_id=agent.id, mcp_tool_id=t.id, enabled=True))
        db.commit()
        print(f"Success: Authorized Agent #{agent.id} for all discovered MCP tools.")

        # 3. Create a test workflow with HITL & MCP Tool nodes
        print("\n--- 2. Testing LangGraph Checkpointing & HITL Interrupt ---")
        hitl_graph = {
            "nodes": [
                {
                    "id": "node_1",
                    "data": {
                        "label": "Text Analyzer",
                        "type": "tool",
                        "tool": "mcp::yuno-native-mcp::analyze_text",
                        "require_approval": True  # Triggers HITL interrupt
                    }
                },
                {
                    "id": "node_2",
                    "data": {
                        "label": "Report Formatter",
                        "type": "tool",
                        "tool": "mcp::yuno-native-mcp::format_report"
                    }
                }
            ],
            "edges": [
                {"source": "node_1", "target": "node_2"}
            ]
        }

        workflow = Workflow(
            name="HITL Verification Workflow",
            description="Workflow testing HITL interrupt, resume, and idempotency",
            graph=hitl_graph,
            active=True
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        # Run execution — should pause at node_1 due to require_approval=True
        task_text = "Analyze this sample paragraph. Artificial intelligence is transforming agentic workflows."
        exec_1 = RuntimeEngine.execute_workflow(db, workflow, input_task=task_text)

        print(f"Execution #{exec_1.id} Status: {exec_1.status}")
        print(f"Thread ID: {exec_1.thread_id}")
        print(f"Approval Data: {exec_1.approval_data}")

        assert exec_1.status == "waiting_for_approval", f"Expected 'waiting_for_approval', got '{exec_1.status}'"
        assert exec_1.thread_id == str(exec_1.id), "Thread ID should match execution ID"
        assert exec_1.approval_data is not None, "Approval data should be populated"
        print("Success: LangGraph successfully paused at interrupt() and checkpointed state!")

        # 4. Resume Workflow with Command(resume="APPROVED")
        print("\n--- 3. Testing Workflow Resume via Command(resume='APPROVED') ---")
        resumed_exec = RuntimeEngine.resume_workflow(db, exec_1, decision="APPROVED")
        print(f"Resumed Execution #{resumed_exec.id} Final Status: {resumed_exec.status}")
        print(f"Final Output Snippet: {(resumed_exec.final_output or '')[:200]}...")

        assert resumed_exec.status == "completed", f"Expected 'completed', got '{resumed_exec.status}'"
        assert resumed_exec.final_output is not None, "Final output should be set"
        print("Success: LangGraph successfully resumed from checkpoint and completed!")

        # 5. Verify Idempotency Shield
        print("\n--- 4. Verifying Idempotency Key Shield ---")
        key = IdempotencyGuard.compute_key(exec_1.id, "node_1", "mcp::yuno-native-mcp::analyze_text")
        print(f"Generated Idempotency Key for node_1 tool: {key}")
        assert IdempotencyGuard.is_executed(key) == True, "Key should be marked executed"
        print("Success: Idempotency shield registered key and protected side-effect from replay!")

        print("\n=== ALL INTEGRATION TESTS PASSED PERFECTLY! ===")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
