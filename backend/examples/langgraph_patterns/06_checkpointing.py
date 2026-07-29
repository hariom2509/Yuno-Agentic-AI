"""
Concept 06: Checkpointing & State Persistence in LangGraph
Demonstrates:
1. In-memory checkpointer (MemorySaver)
2. State history snapshotting and thread checkpoint namespace
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
import operator


class CheckpointState(TypedDict):
    step_count: int
    logs: Annotated[List[str], operator.add]


def step_one_node(state: CheckpointState) -> dict:
    return {
        "step_count": state["step_count"] + 1,
        "logs": [f"Step 1 executed. Current step count: {state['step_count'] + 1}"],
    }


def step_two_node(state: CheckpointState) -> dict:
    return {
        "step_count": state["step_count"] + 1,
        "logs": [f"Step 2 executed. Current step count: {state['step_count'] + 1}"],
    }


def test_memory_checkpointer():
    # 1. In-Memory Checkpointer (Development / Testing)
    memory_checkpointer = MemorySaver()
    
    builder = StateGraph(CheckpointState)
    builder.add_node("step1", step_one_node)
    builder.add_node("step2", step_two_node)
    builder.add_edge(START, "step1")
    builder.add_edge("step1", "step2")
    builder.add_edge("step2", END)

    graph = builder.compile(checkpointer=memory_checkpointer)
    config = {"configurable": {"thread_id": "thread_demo_101"}}

    # Execute graph with thread_id
    res1 = graph.invoke({"step_count": 0, "logs": ["Started graph"]}, config)
    assert res1["step_count"] == 2
    assert len(res1["logs"]) == 3

    # Inspect state snapshot from checkpointer using thread_id
    snapshot = graph.get_state(config)
    assert snapshot.values["step_count"] == 2
    
    print("MemorySaver Checkpointing Test Passed!")
    print("Checkpoint History Snapshot Values:", snapshot.values)
    print("Concept 06 (Checkpointing & State Persistence) Passed Successfully!")


if __name__ == "__main__":
    test_memory_checkpointer()
