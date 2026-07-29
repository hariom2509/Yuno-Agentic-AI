"""
Concept 15: Layered Retry Ownership in LangGraph
Demonstrates RetryPolicy for node-level transient failures without triggering exponential retry explosion across Celery/MCP layers
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
import time

attempt_counter = {"flakey_node": 0}


class RetryState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    retry_count: int


def flakey_network_node(state: RetryState) -> dict:
    attempt_counter["flakey_node"] += 1
    count = attempt_counter["flakey_node"]
    
    # Simulate transient network failure on first 2 attempts
    if count < 3:
        print(f" -> [Flakey Node Attempt {count}] Simulating transient 503 error...")
        raise TimeoutError(f"Transient HTTP 503 Timeout on attempt {count}")

    print(f" -> [Flakey Node Attempt {count}] Network connection succeeded!")
    return {
        "retry_count": count,
        "messages": [AIMessage(content=f"Succeeded on attempt {count}", name="FlakeyNode")]
    }


def build_retry_policy_graph():
    builder = StateGraph(RetryState)

    # Attach LangGraph RetryPolicy with max_attempts=3 and exponential backoff
    retry_policy = RetryPolicy(
        retry_on=TimeoutError,
        max_attempts=3,
        initial_interval=0.1,
        backoff_factor=2.0
    )

    builder.add_node("flakey_node", flakey_network_node, retry=retry_policy)

    builder.add_edge(START, "flakey_node")
    builder.add_edge("flakey_node", END)

    return builder.compile()


def test_retry_ownership():
    graph = build_retry_policy_graph()

    res = graph.invoke({
        "messages": [HumanMessage(content="Fetch remote telemetry")],
        "retry_count": 0
    })

    assert attempt_counter["flakey_node"] == 3
    assert res["retry_count"] == 3
    assert "Succeeded on attempt 3" in res["messages"][-1].content

    print("Concept 15 (Layered Retry Ownership & Node RetryPolicy) Passed Successfully!")


if __name__ == "__main__":
    test_retry_ownership()
