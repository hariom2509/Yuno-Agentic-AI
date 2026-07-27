"""
Concept 14: Parallel Fan-Out / Fan-In Aggregation Pattern
Demonstrates static concurrent execution across Security, Cost, and Performance branches merging into a single Aggregator node
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
import operator

class FanOutState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    analysis_reports: Annotated[List[str], operator.add]


# 1. Branch Node: Security Analysis
def security_branch_node(state: FanOutState) -> dict:
    return {
        "analysis_reports": ["Security Analysis: 0 vulnerabilities found in dependency graph."],
        "messages": [AIMessage(content="Security Audit Completed", name="SecurityAuditor")]
    }


# 2. Branch Node: Cost Analysis
def cost_branch_node(state: FanOutState) -> dict:
    return {
        "analysis_reports": ["Cost Analysis: Estimated monthly API cost $12.50."],
        "messages": [AIMessage(content="Cost Audit Completed", name="CostAuditor")]
    }


# 3. Branch Node: Performance Analysis
def performance_branch_node(state: FanOutState) -> dict:
    return {
        "analysis_reports": ["Performance Analysis: Average latency 45ms per graph step."],
        "messages": [AIMessage(content="Performance Audit Completed", name="PerfAuditor")]
    }


# 4. Aggregator Node receiving merged parallel outputs
def aggregator_node(state: FanOutState) -> dict:
    reports = state.get("analysis_reports", [])
    count = len(reports)
    summary = f"Aggregated Platform Report ({count} audit branches complete):\n" + "\n".join(f" - {r}" for r in reports)
    return {
        "messages": [AIMessage(content=summary, name="Aggregator")]
    }


def build_parallel_fanout_graph():
    builder = StateGraph(FanOutState)

    builder.add_node("security_branch", security_branch_node)
    builder.add_node("cost_branch", cost_branch_node)
    builder.add_node("performance_branch", performance_branch_node)
    builder.add_node("aggregator", aggregator_node)

    # Static Fan-Out from START to all 3 parallel nodes
    builder.add_edge(START, "security_branch")
    builder.add_edge(START, "cost_branch")
    builder.add_edge(START, "performance_branch")

    # Static Fan-In merging all 3 branches into Aggregator
    builder.add_edge("security_branch", "aggregator")
    builder.add_edge("cost_branch", "aggregator")
    builder.add_edge("performance_branch", "aggregator")
    builder.add_edge("aggregator", END)

    return builder.compile()


def test_parallel_fanout():
    graph = build_parallel_fanout_graph()

    res = graph.invoke({
        "messages": [HumanMessage(content="Run full platform audit")],
        "analysis_reports": []
    })

    assert len(res["analysis_reports"]) == 3
    assert len(res["messages"]) == 5  # Human + 3 Workers + Aggregator
    assert res["messages"][-1].name == "Aggregator"

    print("Concept 14 (Parallel Fan-Out / Fan-In Aggregation) Passed Successfully!")
    print("Final Aggregated Summary:\n", res["messages"][-1].content)


if __name__ == "__main__":
    test_parallel_fanout()
