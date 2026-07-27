"""
Concept 16: Token & Event Streaming in LangGraph (astream_events)
Demonstrates async streaming of node events and token chunks for WebSocket UI listeners
"""

import asyncio
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

class StreamState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


async def streaming_agent_node(state: StreamState) -> dict:
    # Simulates token streaming step
    return {
        "messages": [AIMessage(content="Streaming complete response token by token.", name="StreamAgent")]
    }


def build_stream_graph():
    builder = StateGraph(StreamState)
    builder.add_node("stream_agent", streaming_agent_node)
    builder.add_edge(START, "stream_agent")
    builder.add_edge("stream_agent", END)
    return builder.compile()


async def test_event_streaming():
    graph = build_stream_graph()
    captured_events = []

    # Stream graph events using astream_events API
    async for event in graph.astream_events({"messages": [HumanMessage(content="Stream request")]}, version="v2"):
        kind = event.get("event")
        name = event.get("name")
        captured_events.append(f"{kind}:{name}")

    assert len(captured_events) > 0
    print("Concept 16 (Token & Node Event Streaming) Passed Successfully!")
    print(f"Captured {len(captured_events)} Stream Events:")
    for ev in captured_events[:8]:
        print(f" - {ev}")


if __name__ == "__main__":
    asyncio.run(test_event_streaming())
