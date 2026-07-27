"""
Concept 12: Supervisor Multi-Agent Pattern
Demonstrates central Supervisor orchestrator delegating to specialized workers and receiving control back after each step
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

class SupervisorState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_worker: str
    completed_workers: List[str]


# 1. Central Supervisor Node
def supervisor_node(state: SupervisorState) -> dict:
    completed = state.get("completed_workers", [])
    
    # Deterministic / Structured Supervisor logic
    if "researcher" not in completed:
        return {
            "next_worker": "researcher",
            "messages": [AIMessage(content="Supervisor: Delegating step 1 to Researcher.", name="Supervisor")]
        }
    elif "coder" not in completed:
        return {
            "next_worker": "coder",
            "messages": [AIMessage(content="Supervisor: Delegating step 2 to Coder.", name="Supervisor")]
        }
    else:
        return {
            "next_worker": "FINISH",
            "messages": [AIMessage(content="Supervisor: All tasks complete. Finalizing output.", name="Supervisor")]
        }


# 2. Worker Nodes
def researcher_worker_node(state: SupervisorState) -> dict:
    completed = state.get("completed_workers", []) + ["researcher"]
    return {
        "completed_workers": completed,
        "messages": [AIMessage(content="Researcher: Gathered benchmark data.", name="Researcher")]
    }


def coder_worker_node(state: SupervisorState) -> dict:
    completed = state.get("completed_workers", []) + ["coder"]
    return {
        "completed_workers": completed,
        "messages": [AIMessage(content="Coder: Implemented algorithm code.", name="Coder")]
    }


# Router evaluating Supervisor's next_worker directive
def supervisor_routing_fn(state: SupervisorState) -> str:
    next_target = state.get("next_worker", "FINISH")
    if next_target == "researcher":
        return "researcher"
    elif next_target == "coder":
        return "coder"
    return END


def build_supervisor_graph():
    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor", supervisor_node)
    builder.add_node("researcher", researcher_worker_node)
    builder.add_node("coder", coder_worker_node)

    builder.add_edge(START, "supervisor")
    
    # Conditional routing from Supervisor to Worker or END
    builder.add_conditional_edges("supervisor", supervisor_routing_fn, {
        "researcher": "researcher",
        "coder": "coder",
        END: END
    })

    # Crucial Supervisor Pattern invariant: Workers loop back to Supervisor!
    builder.add_edge("researcher", "supervisor")
    builder.add_edge("coder", "supervisor")

    return builder.compile()


def test_supervisor_pattern():
    graph = build_supervisor_graph()

    res = graph.invoke({
        "messages": [HumanMessage(content="Build benchmark report and code implementation")],
        "next_worker": "",
        "completed_workers": []
    })

    assert "researcher" in res["completed_workers"]
    assert "coder" in res["completed_workers"]
    assert res["next_worker"] == "FINISH"

    print("Concept 12 (Supervisor Multi-Agent Pattern) Passed Successfully!")
    print("Execution Message Trail:")
    for m in res["messages"]:
        print(f" - [{getattr(m, 'name', 'user')}] {m.content}")


if __name__ == "__main__":
    test_supervisor_pattern()
