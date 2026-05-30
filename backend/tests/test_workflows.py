def test_create_workflow(client):
    payload = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "graph": {"nodes": [], "edges": []}
    }
    response = client.post("/workflows/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Workflow"
    assert data["graph"] == {"nodes": [], "edges": []}

def test_get_workflows(client):
    payload = {
        "name": "Test Workflow 2",
        "description": "A test workflow",
        "graph": {"nodes": [], "edges": []}
    }
    client.post("/workflows/", json=payload)
    
    response = client.get("/workflows/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_deploy_template(client):
    response = client.post("/templates/research_workflow/deploy")
    assert response.status_code == 200
    data = response.json()
    assert "workflow_id" in data
    
    # Verify the workflow was created
    wf_resp = client.get(f"/workflows/{data['workflow_id']}")
    assert wf_resp.status_code == 200
    assert wf_resp.json()["name"] == "Research & Analysis Workflow"