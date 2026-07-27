"""
Concept 05: Dynamic Parallel Execution with Send API vs Static Parallelism
Demonstrates:
1. Static Parallelism: Known graph topology at compile time
2. Dynamic Send API: Runtime-determined map-reduce fan-out via conditional edge Send() returns
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator

# State for Dynamic Send Execution
class DynamicSendState(TypedDict):
    documents: List[str]
    processed_results: Annotated[List[str], operator.add]


# State for Worker Node
class WorkerState(TypedDict):
    document: str


# 1. Map Node: Initializes task payload
def map_dispatcher_node(state: DynamicSendState) -> dict:
    # Node action before dynamic fan-out
    return {"processed_results": ["Map Dispatcher initialized dynamic jobs"]}


# 2. Conditional Edge Router returning List[Send] for dynamic fan-out
def continue_to_workers(state: DynamicSendState) -> List[Send]:
    docs = state.get("documents", [])
    # Returns dynamic Send targets for runtime variable array
    return [Send("document_processor_worker", {"document": doc}) for doc in docs]


# 3. Worker Node receiving single dynamic Send payload
def document_processor_worker(state: WorkerState) -> dict:
    doc = state["document"]
    processed = f"Processed document '{doc}' (length: {len(doc)} chars)"
    return {"processed_results": [processed]}


# 4. Aggregator Node receiving all fan-in results
def aggregator_node(state: DynamicSendState) -> dict:
    count = len(state["processed_results"]) - 1  # Exclude init log
    summary = f"Successfully aggregated {count} dynamic document worker results."
    return {"processed_results": [summary]}


def build_dynamic_send_graph():
    builder = StateGraph(DynamicSendState)

    builder.add_node("map_dispatcher", map_dispatcher_node)
    builder.add_node("document_processor_worker", document_processor_worker)
    builder.add_node("aggregator", aggregator_node)

    builder.add_edge(START, "map_dispatcher")
    
    # Conditional edge using continue_to_workers returning List[Send]
    builder.add_conditional_edges("map_dispatcher", continue_to_workers, ["document_processor_worker"])
    
    builder.add_edge("document_processor_worker", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile()


def test_dynamic_send():
    graph = build_dynamic_send_graph()
    
    # Test dynamic runtime fan-out over 4 documents
    input_data: DynamicSendState = {
        "documents": [
            "Doc 1: Enterprise Market Shift",
            "Doc 2: LangGraph Checkpoint Durability",
            "Doc 3: PostgreSQL Reducer Channels",
            "Doc 4: Model Context Protocol Specification"
        ],
        "processed_results": []
    }

    res = graph.invoke(input_data)

    # 1 Init + 4 Workers + 1 Aggregator summary = 6
    assert len(res["processed_results"]) == 6
    assert "aggregated 4 dynamic document" in res["processed_results"][-1].lower()

    print("Concept 05 (Dynamic Send API & Parallel Map-Reduce) Passed Successfully!")
    print("Processed Results:")
    for r in res["processed_results"]:
        print(f" - {r}")


if __name__ == "__main__":
    test_dynamic_send()
