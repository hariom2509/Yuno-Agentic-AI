import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.agent import Agent
from app.models.mcp_server import MCPServer, MCPTool, AgentMCPTool
from app.mcp.adapter import MCPToolAdapter
from app.mcp.authorization import MCPAuthorizationService
from app.mcp.exceptions import MCPAuthorizationError, MCPSecurityError
from app.mcp.manager import MCPManager
from app.mcp.registry import MCPToolRegistry
from app.runtime.tool_executor import ToolExecutor


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_mcp_server_and_tool_creation(db_session):
    server = MCPServer(
        name="github-mcp",
        description="GitHub Integration MCP Server",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        enabled=True,
    )
    db_session.add(server)
    db_session.commit()
    db_session.refresh(server)

    tool = MCPTool(
        server_id=server.id,
        name="create_issue",
        description="Creates a GitHub issue",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["title"],
        },
        enabled=True,
    )
    db_session.add(tool)
    db_session.commit()

    assert server.id is not None
    assert len(server.tools) == 1
    assert server.tools[0].name == "create_issue"


def test_openai_tool_adapter(db_session):
    tool = MCPTool(
        server_id=1,
        name="search_repo",
        description="Search repository code",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
    )
    adapted = MCPToolAdapter.to_openai_function(tool, server_name="github")

    assert adapted["type"] == "function"
    assert adapted["function"]["name"] == "mcp::github::search_repo"
    assert adapted["function"]["description"] == "Search repository code"
    assert "query" in adapted["function"]["parameters"]["properties"]


def test_mcp_authorization(db_session):
    # Setup Agent
    agent = Agent(name="Dev Agent", role="Developer", system_prompt="Code helper")
    db_session.add(agent)
    db_session.commit()

    # Setup MCP Server & Tools
    server = MCPServer(name="jira-mcp", transport="stdio", command="python", enabled=True)
    db_session.add(server)
    db_session.commit()

    tool1 = MCPTool(server_id=server.id, name="read_ticket", enabled=True)
    tool2 = MCPTool(server_id=server.id, name="delete_ticket", enabled=True)
    db_session.add_all([tool1, tool2])
    db_session.commit()

    # Authorize tool1 ONLY for agent
    assign = AgentMCPTool(agent_id=agent.id, mcp_tool_id=tool1.id, enabled=True)
    db_session.add(assign)
    db_session.commit()

    # Authorized check should pass
    verified = MCPAuthorizationService.verify_agent_tool_access(db_session, agent.id, "jira-mcp", "read_ticket")
    assert verified.id == tool1.id

    # Unauthorized check should raise MCPAuthorizationError
    with pytest.raises(MCPAuthorizationError):
        MCPAuthorizationService.verify_agent_tool_access(db_session, agent.id, "jira-mcp", "delete_ticket")


def test_command_allowlist_security(db_session):
    server = MCPServer(name="malicious-mcp", transport="stdio", command="rm", args=["-rf", "/"], enabled=True)
    db_session.add(server)
    db_session.commit()

    with pytest.raises(MCPSecurityError):
        MCPManager.get_session(db_session, "malicious-mcp")


def test_tool_executor_mcp_dispatch(db_session):
    agent = Agent(name="Ops Agent", role="Operations", system_prompt="Ops bot")
    db_session.add(agent)
    db_session.commit()

    server = MCPServer(name="ops-mcp", transport="stdio", command="python", args=["-m", "ops"], enabled=True)
    db_session.add(server)
    db_session.commit()

    tool = MCPTool(server_id=server.id, name="get_metrics", enabled=True)
    db_session.add(tool)
    db_session.commit()

    assign = AgentMCPTool(agent_id=agent.id, mcp_tool_id=tool.id, enabled=True)
    db_session.add(assign)
    db_session.commit()

    res = ToolExecutor.execute(
        tool_name="mcp::ops-mcp::get_metrics",
        payload={"service": "api"},
        db=db_session,
        agent_id=agent.id,
    )
    assert "ops-mcp" in res or "Executed" in res or "success" in res.lower()
