"""
Concept 02: Reducers and Parallel State Updates in LangGraph
Demonstrates:
1. Message-specific reducer (`add_messages` from langgraph.graph.message)
2. Parallel state updates across concurrent nodes using reducers
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

# State definition with reducers for parallel channel writes
class ParallelState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    logs: Annotated[List[str], operator.add]


# Node 1: Worker A running in parallel
def worker_a_node(state: ParallelState) -> dict:
    return {
        "messages": [AIMessage(content="Worker A complete", name="WorkerA")],
        "logs": ["Worker A finished task component 1"],
    }


# Node 2: Worker B running in parallel
def worker_b_node(state: ParallelState) -> dict:
    return {
        "messages": [AIMessage(content="Worker B complete", name="WorkerB")],
        "logs": ["Worker B finished task component 2"],
    }


# Aggregator node receiving merged parallel state
def aggregator_node(state: ParallelState) -> dict:
    log_count = len(state["logs"])
    msg_count = len(state["messages"])
    summary = f"Aggregated {log_count} log entries and {msg_count} messages."
    return {
        "messages": [AIMessage(content=summary, name="Aggregator")],
        "logs": [summary],
    }


def build_parallel_reducer_graph():
    builder = StateGraph(ParallelState)
    
    builder.add_node("worker_a", worker_a_node)
    builder.add_node("worker_b", worker_b_node)
    builder.add_node("aggregator", aggregator_node)

    # Parallel fan-out from START to Worker A and Worker B
    builder.add_edge(START, "worker_a")
    builder.add_edge(START, "worker_b")

    # Fan-in aggregation
    builder.add_edge("worker_a", "aggregator")
    builder.add_edge("worker_b", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile()


def test_parallel_reducers():
    graph = build_parallel_reducer_graph()
    initial_input: ParallelState = {
        "messages": [HumanMessage(content="Start parallel jobs")],
        "logs": ["Job started"],
    }

    final_state = graph.invoke(initial_input)

    # Verify add_messages and operator.add correctly merged parallel updates
    assert len(final_state["messages"]) == 4  # Initial + WorkerA + WorkerB + Aggregator
    assert len(final_state["logs"]) == 4      # Initial + WorkerA + WorkerB + Aggregator summary
    
    print("Concept 02 (Reducers & Parallel Channel Updates) Test Passed Successfully!")
    print("Final Messages Sequence:")
    for m in final_state["messages"]:
        print(f" - [{m.type.upper()}] {getattr(m, 'name', 'user')}: {m.content}")


if __name__ == "__main__":
    test_parallel_reducers()
