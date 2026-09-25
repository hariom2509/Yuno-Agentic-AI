def test_create_agent(client):
    payload = {
        "name": "Test Agent",
        "role": "Tester",
        "system_prompt": "You are a test agent",
        "model": "gpt-4o-mini",
        "temperature": 0.5,
        "guardrails": {"blocked_topics": ["test"]}
    }
    response = client.post("/agents/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["temperature"] == 0.5
    assert "test" in data["guardrails"]["blocked_topics"]
    assert data["active"] is True

def test_get_agents(client):
    payload = {
        "name": "Test Agent 2",
        "role": "Tester",
        "system_prompt": "You are a test agent",
    }
    client.post("/agents/", json=payload)
    
    response = client.get("/agents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(a["name"] == "Test Agent 2" for a in data)

def test_update_agent(client):
    payload = {
        "name": "Test Agent 3",
        "role": "Tester",
        "system_prompt": "You are a test agent",
    }
    create_resp = client.post("/agents/", json=payload)
    agent_id = create_resp.json()["id"]

    update_payload = {"name": "Updated Agent"}
    update_resp = client.put(f"/agents/{agent_id}", json=update_payload)
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated Agent"

def test_delete_agent(client):
    payload = {
        "name": "Test Agent 4",
        "role": "Tester",
        "system_prompt": "You are a test agent",
    }
    create_resp = client.post("/agents/", json=payload)
    agent_id = create_resp.json()["id"]

    del_resp = client.delete(f"/agents/{agent_id}")
    assert del_resp.status_code == 204

    # Ensure it's soft deleted
    get_resp = client.get("/agents/")
    assert not any(a["id"] == agent_id for a in get_resp.json())


def test_agent_explicit_tool_assignment(client, db_session):
    from app.models.mcp_server import MCPServer, MCPTool

    # 1. Create MCP server and tool
    server = MCPServer(name="test-server", transport="stdio", command="python", enabled=True)
    db_session.add(server)
    db_session.commit()

    tool = MCPTool(
        server_id=server.id,
        name="test_tool",
        exposure="AGENT_ASSIGNABLE",
        risk_level="HIGH",
        requires_approval=True,
        enabled=True
    )
    db_session.add(tool)
    db_session.commit()

    # 2. Create agent -> verify NO auto-seeding
    create_resp = client.post("/agents/", json={
        "name": "Secure Agent",
        "role": "Analyst",
        "system_prompt": "Analyze things securely",
    })
    assert create_resp.status_code == 201
    agent_id = create_resp.json()["id"]

    tools_resp = client.get(f"/agents/{agent_id}/mcp-tools")
    assert tools_resp.status_code == 200
    assert len(tools_resp.json()) == 0, "New agents must not be auto-seeded with tools"

    # 3. Explicitly assign tool to agent
    assign_resp = client.post(f"/agents/{agent_id}/mcp-tools", json={
        "mcp_tool_ids": [tool.id]
    })
    assert assign_resp.status_code == 200
    assert tool.id in assign_resp.json()["assigned_mcp_tool_ids"]

    # 4. Verify agent now has the assigned tool
    tools_resp2 = client.get(f"/agents/{agent_id}/mcp-tools")
    assert len(tools_resp2.json()) == 1
    assert tools_resp2.json()[0]["tool_name"] == "test_tool"

    # 5. Admin tool management endpoints
    manage_resp = client.get("/api/mcp-servers/tools/manage")
    assert manage_resp.status_code == 200
    assert any(t["id"] == tool.id for t in manage_resp.json())

    # Update tool risk & approval
    update_resp = client.put(f"/api/mcp-servers/tools/{tool.id}", json={
        "risk_level": "CRITICAL",
        "requires_approval": True,
        "exposure": "AGENT_ASSIGNABLE"
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["tool"]["risk_level"] == "CRITICAL"