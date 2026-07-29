"""
Concept 10: Subgraphs & Nested Graph Composition in LangGraph
Demonstrates compiling an independent subgraph and embedding it as a node inside a parent graph
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

# Parent Graph State
class ParentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    research_summary: str


# Subgraph Private State
class ResearchSubgraphState(TypedDict):
    query: str
    raw_results: List[str]
    summary: str


# --- Subgraph Node Definitions ---
def search_node(state: ResearchSubgraphState) -> dict:
    return {"raw_results": [f"Result 1 for '{state['query']}'", f"Result 2 for '{state['query']}'"]}


def summarize_node(state: ResearchSubgraphState) -> dict:
    count = len(state.get("raw_results", []))
    return {"summary": f"Synthesized research summary over {count} search results."}


def build_research_subgraph():
    builder = StateGraph(ResearchSubgraphState)
    builder.add_node("search", search_node)
    builder.add_node("summarize", summarize_node)
    builder.add_edge(START, "search")
    builder.add_edge("search", "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


# --- Parent Graph Node Definitions ---
def parent_input_node(state: ParentState) -> dict:
    return {"messages": [AIMessage(content="Parent Initiating Research Subgraph Call...", name="Parent")]}


# Wrapper node that invokes the compiled Subgraph
def call_research_subgraph_wrapper(state: ParentState) -> dict:
    subgraph = build_research_subgraph()
    
    # Map parent state to subgraph input state
    subgraph_input: ResearchSubgraphState = {
        "query": state["messages"][0].content,
        "raw_results": [],
        "summary": ""
    }
    
    subgraph_output = subgraph.invoke(subgraph_input)
    
    # Return mapped state update to parent graph
    return {
        "research_summary": subgraph_output["summary"],
        "messages": [AIMessage(content=f"Subgraph Output: {subgraph_output['summary']}", name="ResearchSubgraph")]
    }


def parent_final_report_node(state: ParentState) -> dict:
    summary = state.get("research_summary", "")
    return {"messages": [AIMessage(content=f"Final Parent Report: {summary}", name="Parent")]}


def build_parent_graph():
    builder = StateGraph(ParentState)
    builder.add_node("parent_input", parent_input_node)
    builder.add_node("research_subgraph_node", call_research_subgraph_wrapper)
    builder.add_node("parent_final_report", parent_final_report_node)

    builder.add_edge(START, "parent_input")
    builder.add_edge("parent_input", "research_subgraph_node")
    builder.add_edge("research_subgraph_node", "parent_final_report")
    builder.add_edge("parent_final_report", END)

    return builder.compile()


def test_subgraphs():
    parent_graph = build_parent_graph()
    res = parent_graph.invoke({
        "messages": [HumanMessage(content="Investigate LangGraph Subgraph Composition")],
        "research_summary": ""
    })

    assert res["research_summary"] != ""
    assert "Synthesized research summary over 2 search results" in res["research_summary"]
    assert res["messages"][-1].name == "Parent"

    print("Concept 10 (Subgraphs & Nested Graph Composition) Passed Successfully!")
    print("Final Parent Output Summary:", res["research_summary"])


if __name__ == "__main__":
    test_subgraphs()
