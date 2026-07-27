"""
Concept 18: Idempotency Keys for Side-Effecting Tools & Recursion Circuit Breakers
Demonstrates:
1. Idempotency Key computation (execution_id + node_id + tool_call_id) preventing duplicate side-effects on replay/resumption
2. Graph Recursion Limit circuit breaker
"""

from typing import TypedDict, Annotated, List, Set
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError
import hashlib

executed_idempotency_keys: Set[str] = set()


class IdempotencyState(TypedDict):
    execution_id: int
    node_id: str
    tool_call_id: str
    action_log: List[str]
    iteration_counter: int


def compute_idempotency_key(execution_id: int, node_id: str, tool_call_id: str) -> str:
    """Computes deterministic SHA-256 idempotency key for side-effecting tools."""
    raw = f"{execution_id}:{node_id}:{tool_call_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def side_effect_tool_node(state: IdempotencyState) -> dict:
    key = compute_idempotency_key(state["execution_id"], state["node_id"], state["tool_call_id"])
    
    # Check if this exact tool invocation has already executed
    if key in executed_idempotency_keys:
        print(f" -> [Idempotency Shield] Key '{key}' already executed! Skipping duplicate side-effect.")
        return {"action_log": state["action_log"] + [f"Skipped duplicate side-effect (key: {key})"]}

    # Execute side-effect tool
    executed_idempotency_keys.add(key)
    print(f" -> [Side-Effect Executed] Key '{key}' registered.")
    return {"action_log": state["action_log"] + [f"Executed side-effect (key: {key})"]}


def infinite_loop_node(state: IdempotencyState) -> dict:
    return {"iteration_counter": state["iteration_counter"] + 1}


def build_idempotency_graph():
    builder = StateGraph(IdempotencyState)
    builder.add_node("side_effect_tool", side_effect_tool_node)
    builder.add_edge(START, "side_effect_tool")
    builder.add_edge("side_effect_tool", END)
    return builder.compile()


def build_loop_graph():
    builder = StateGraph(IdempotencyState)
    builder.add_node("loop_node", infinite_loop_node)
    builder.add_edge(START, "loop_node")
    # Intentional infinite cycle
    builder.add_edge("loop_node", "loop_node")
    return builder.compile()


def test_idempotency_and_circuit_breaker():
    # 1. Test Idempotency Shield
    graph_idemp = build_idempotency_graph()
    payload = {
        "execution_id": 999,
        "node_id": "github_issue_creator",
        "tool_call_id": "call_create_issue_001",
        "action_log": [],
        "iteration_counter": 0
    }

    # Run 1: First Execution
    res1 = graph_idemp.invoke(payload)
    assert len(res1["action_log"]) == 1
    assert "Executed side-effect" in res1["action_log"][0]

    # Run 2: Replay / Crash Resumption with SAME key
    res2 = graph_idemp.invoke(payload)
    assert len(res2["action_log"]) == 1
    assert "Skipped duplicate side-effect" in res2["action_log"][0]
    print("Idempotency Key Shield Test Passed!")

    # 2. Test Recursion Limit Circuit Breaker
    loop_graph = build_loop_graph()
    try:
        # Config recursion_limit=5 to trigger GraphRecursionError
        loop_graph.invoke({
            "execution_id": 1,
            "node_id": "loop",
            "tool_call_id": "0",
            "action_log": [],
            "iteration_counter": 0
        }, config={"recursion_limit": 5})
        assert False, "Should have raised GraphRecursionError"
    except GraphRecursionError:
        print("Recursion Circuit Breaker Test Passed (GraphRecursionError caught successfully)!")

    print("Concept 18 (Idempotency Keys & Recursion Circuit Breakers) Passed Successfully!")


if __name__ == "__main__":
    test_idempotency_and_circuit_breaker()
