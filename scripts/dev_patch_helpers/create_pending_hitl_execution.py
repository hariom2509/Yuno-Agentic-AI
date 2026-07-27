import os
import sys
from app.db.database import SessionLocal, Base, engine
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.models.execution import Execution
from app.models.mcp_server import MCPServer, MCPTool, AgentMCPTool
from app.runtime.runtime_engine import RuntimeEngine

def create_hitl():
    db = SessionLocal()
    try:
        # Seed server & tools
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

        from app.mcp.registry import MCPToolRegistry
        tools = MCPToolRegistry.discover_and_cache_tools(db, server)

        # Create workflow with HITL approval step
        hitl_graph = {
            "nodes": [
                {
                    "id": "security_check_node",
                    "data": {
                        "label": "Security Vulnerability Scanner",
                        "type": "tool",
                        "tool": "mcp::yuno-native-mcp::analyze_text",
                        "require_approval": True
                    }
                },
                {
                    "id": "formatter_node",
                    "data": {
                        "label": "Executive Summary Formatter",
                        "type": "tool",
                        "tool": "mcp::yuno-native-mcp::format_report"
                    }
                }
            ],
            "edges": [
                {"source": "security_check_node", "target": "formatter_node"}
            ]
        }

        workflow = db.query(Workflow).filter(Workflow.name == "Interactive UI HITL Approval Workflow").first()
        if not workflow:
            workflow = Workflow(
                name="Interactive UI HITL Approval Workflow",
                description="Workflow with Human-In-The-Loop approval node for testing UI interactions",
                graph=hitl_graph,
                active=True
            )
            db.add(workflow)
            db.commit()
            db.refresh(workflow)

        print(f"Workflow created/found: #{workflow.id} - '{workflow.name}'")

        # Execute workflow — will pause at security_check_node and enter waiting_for_approval
        exec_record = RuntimeEngine.execute_workflow(
            db,
            workflow,
            input_task="Perform automated security audit on production infrastructure."
        )

        print(f"Execution #{exec_record.id} created with Status: '{exec_record.status}'")
        print(f"Thread ID: {exec_record.thread_id}")
        print(f"Approval Data: {exec_record.approval_data}")
        return exec_record.id
    finally:
        db.close()

if __name__ == "__main__":
    create_hitl()
