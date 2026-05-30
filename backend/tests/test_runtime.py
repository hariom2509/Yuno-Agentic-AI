from app.runtime.runtime_engine import RuntimeEngine
from app.models.workflow import Workflow

def test_default_workflow_execution(db_session, mock_openai):
    workflow = Workflow(name="Test default", graph={})
    db_session.add(workflow)
    db_session.commit()

    execution = RuntimeEngine.execute_workflow(db_session, workflow, "Test task")
    assert execution.status == "completed"
    assert "Final Report" in execution.final_output or "AI Analysis Report" in execution.final_output
    assert execution.tokens_used > 0
    assert execution.cost_usd > 0

def test_graph_workflow_execution(db_session, mock_openai):
    graph = {
        "nodes": [
            {"id": "n1", "data": {"label": "Agent 1", "type": "agent", "memory_enabled": False}},
            {"id": "n2", "data": {"label": "Agent 2", "type": "agent", "memory_enabled": False}}
        ],
        "edges": [
            {"source": "n1", "target": "n2"}
        ]
    }
    workflow = Workflow(name="Test graph", graph=graph)
    db_session.add(workflow)
    db_session.commit()

    execution = RuntimeEngine.execute_workflow(db_session, workflow, "Test task")
    assert execution.status == "completed"
    assert "Mocked AI response" in execution.final_output

def test_guardrails(db_session, mock_openai):
    graph = {
        "nodes": [
            {"id": "n1", "data": {
                "label": "Agent 1", 
                "type": "agent",
                "guardrails": {"blocked_topics": ["forbidden"]}
            }}
        ],
        "edges": []
    }
    workflow = Workflow(name="Test guardrails", graph=graph)
    db_session.add(workflow)
    db_session.commit()

    # Input contains forbidden word
    execution = RuntimeEngine.execute_workflow(db_session, workflow, "This is a forbidden task")
    assert execution.status == "completed"
    # The output from the agent (which is mocked) will be generated, but the input it saw was blocked.
    # Since our mocked OpenAI returns "Mocked AI response", it passes the output check.
    # We just want to ensure it executes without crashing.
    
    # Check messages to see if input was blocked
    from app.models.message import Message
    msgs = db_session.query(Message).filter(Message.execution_id == execution.id).all()
    blocked_msg = any("System Error" in m.content for m in msgs)
    assert blocked_msg is True

def test_calculator_tool():
    from app.tools.calculator_tool import calculate

    # Test standard expression
    assert calculate("2 + 2") == "Result: 4"
    assert calculate("10 / 2") == "Result: 5.0"

    # Test natural language surrounding math
    assert calculate("The answer is 2 + 2.") == "Result: 4"
    assert calculate("Please compute (10 + 5) * 2 for me!") == "Result: 30"

    # Test mixed letters and numbers that don't form a clean expression
    # Should fall back to try parsing the best match or fail gracefully
    assert "Result: 6.44" in calculate("The ratio is 6.44 (29 billion / 4.5 billion)")
    
    # Test completely non-mathematical text
    assert "Calculation error" in calculate("I understand that you want an estimate")