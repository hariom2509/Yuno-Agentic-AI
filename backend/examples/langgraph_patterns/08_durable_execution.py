"""
Concept 08: Durable Execution Semantics & Crash Resumption in LangGraph
Demonstrates process crash recovery by resuming graph execution from checkpoint
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import operator

node_execution_counter = {"node1": 0, "node2": 0}


class DurableState(TypedDict):
    step_history: Annotated[List[str], operator.add]


def node_one(state: DurableState) -> dict:
    node_execution_counter["node1"] += 1
    return {"step_history": [f"Node 1 Executed (run_count: {node_execution_counter['node1']})"]}


def node_two(state: DurableState) -> dict:
    node_execution_counter["node2"] += 1
    return {"step_history": [f"Node 2 Executed (run_count: {node_execution_counter['node2']})"]}


def build_durable_graph(memory):
    builder = StateGraph(DurableState)
    builder.add_node("node1", node_one)
    builder.add_node("node2", node_two)
    
    builder.add_edge(START, "node1")
    builder.add_edge("node1", "node2")
    builder.add_edge("node2", END)
    
    return builder.compile(checkpointer=memory, interrupt_before=["node2"])


def test_durable_resumption():
    memory = MemorySaver()
    graph = build_durable_graph(memory)
    config = {"configurable": {"thread_id": "durable_thread_77"}}

    # Step 1: Run graph until interrupt before node2 (simulating partial execution / crash point)
    res_partial = graph.invoke({"step_history": ["Started Execution"]}, config)
    
    assert node_execution_counter["node1"] == 1
    assert node_execution_counter["node2"] == 0  # Node 2 paused
    print("Partial execution saved to checkpoint at Node 1!")

    # Step 2: Resume graph from checkpoint (Node 1 must NOT execute again)
    res_final = graph.invoke(None, config)

    assert node_execution_counter["node1"] == 1  # Still 1! Reused state!
    assert node_execution_counter["node2"] == 1  # Node 2 executed on resumption
    assert len(res_final["step_history"]) == 3   # Start + Node1 + Node2

    print("Concept 08 (Durable Execution & Crash Resumption) Passed Successfully!")
    print("Final Step History:", res_final["step_history"])


if __name__ == "__main__":
    test_durable_resumption()
