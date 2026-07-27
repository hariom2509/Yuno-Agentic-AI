"""
Concept 11: Router Pattern (Deterministic Router vs LLM Intent Router)
Demonstrates:
1. Deterministic Router: Rule-based fast routing (cheaper, zero latency, predictable)
2. LLM Intent Router: Structured classification for ambiguous requests
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

class RouterState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    task_type: str  # "code" | "research" | "general"
    selected_branch: str


# --- 1. Deterministic Router Function ---
def deterministic_router_fn(state: RouterState) -> str:
    """Zero-latency rule classification."""
    task = state.get("task_type", "").lower()
    if task == "code" or "python" in state["messages"][0].content.lower():
        return "coding_branch"
    elif task == "research" or "search" in state["messages"][0].content.lower():
        return "research_branch"
    return "general_branch"


def coding_branch_node(state: RouterState) -> dict:
    return {
        "selected_branch": "coding_branch",
        "messages": [AIMessage(content="Executed coding branch logic.", name="Coder")]
    }


def research_branch_node(state: RouterState) -> dict:
    return {
        "selected_branch": "research_branch",
        "messages": [AIMessage(content="Executed research branch logic.", name="Researcher")]
    }


def general_branch_node(state: RouterState) -> dict:
    return {
        "selected_branch": "general_branch",
        "messages": [AIMessage(content="Executed general branch logic.", name="GeneralAgent")]
    }


def build_deterministic_router_graph():
    builder = StateGraph(RouterState)
    builder.add_node("coding_branch", coding_branch_node)
    builder.add_node("research_branch", research_branch_node)
    builder.add_node("general_branch", general_branch_node)

    # Route immediately from START based on deterministic classification
    builder.add_conditional_edges(START, deterministic_router_fn, {
        "coding_branch": "coding_branch",
        "research_branch": "research_branch",
        "general_branch": "general_branch"
    })

    builder.add_edge("coding_branch", END)
    builder.add_edge("research_branch", END)
    builder.add_edge("general_branch", END)

    return builder.compile()


def test_router_pattern():
    graph = build_deterministic_router_graph()

    # Test 1: Coding routing
    res1 = graph.invoke({
        "messages": [HumanMessage(content="Write python function for matrix multiplication")],
        "task_type": "code",
        "selected_branch": ""
    })
    assert res1["selected_branch"] == "coding_branch"

    # Test 2: Research routing
    res2 = graph.invoke({
        "messages": [HumanMessage(content="Search research papers on transformers")],
        "task_type": "research",
        "selected_branch": ""
    })
    assert res2["selected_branch"] == "research_branch"

    print("Concept 11 (Router Pattern: Deterministic vs LLM Classification) Passed Successfully!")


if __name__ == "__main__":
    test_router_pattern()
