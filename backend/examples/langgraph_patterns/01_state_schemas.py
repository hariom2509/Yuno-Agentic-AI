"""
Concept 01: State Schemas in LangGraph
Demonstrates production separation of:
1. Input State Schema (WorkflowInput)
2. Internal Graph State Schema (YunoAgentState)
3. Output State Schema (WorkflowOutput)
4. Private Node State (PrivateState)
"""

from typing import TypedDict, List, Dict, Any, Annotated
from pydantic import BaseModel, Field
import operator

# 1. Input State Schema: Raw request payload entering the graph
class WorkflowInput(TypedDict):
    user_request: str
    workflow_id: int
    execution_id: int


# 2. Internal Graph State Schema: Used during graph execution
class YunoAgentState(TypedDict):
    # Core input data
    user_request: str
    workflow_id: int
    execution_id: int
    
    # Internal orchestration channels
    messages: Annotated[List[Dict[str, str]], operator.add]
    current_agent: str
    tool_results: Annotated[List[Dict[str, Any]], operator.add]
    iteration_count: int
    validation_status: str


# 3. Output State Schema: Clean response schema returned to caller/API
class WorkflowOutput(BaseModel):
    result: str = Field(..., description="Final synthesized answer or output report")
    status: str = Field("completed", description="Execution status: completed | failed | interrupted")
    tokens_used: int = Field(0, description="Total tokens consumed across graph nodes")
    cost_usd: float = Field(0.0, description="Total USD cost incurred")


# 4. Private Node State: State isolated to specific subgraph or private calculation
class PrivateWorkerState(TypedDict):
    private_scratchpad: str
    confidence_score: float


def test_state_schema_isolation():
    """Unit test verifying state initialization and schema isolation."""
    raw_input: WorkflowInput = {
        "user_request": "Analyze OpenAI vs Anthropic enterprise positioning",
        "workflow_id": 101,
        "execution_id": 999,
    }

    # Initialize internal graph state from input
    graph_state: YunoAgentState = {
        **raw_input,
        "messages": [{"role": "user", "content": raw_input["user_request"]}],
        "current_agent": "Coordinator",
        "tool_results": [],
        "iteration_count": 1,
        "validation_status": "pending",
    }

    assert graph_state["workflow_id"] == 101
    assert len(graph_state["messages"]) == 1

    # Simulate output synthesis
    output = WorkflowOutput(
        result="Analysis completed: OpenAI leads in ecosystem size; Anthropic leads in safety steering.",
        status="completed",
        tokens_used=450,
        cost_usd=0.0003,
    )

    assert output.status == "completed"
    assert output.tokens_used == 450
    print("Concept 01 (State Schemas) Test Passed Successfully!")


if __name__ == "__main__":
    test_state_schema_isolation()
