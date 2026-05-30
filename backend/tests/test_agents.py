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