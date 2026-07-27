"""
Concept 07: Threads & Conversational Persistence in LangGraph
Demonstrates thread_id binding to checkpoint history across multi-turn sessions
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ChatThreadState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


def chatbot_node(state: ChatThreadState) -> dict:
    last_user_msg = state["messages"][-1].content
    ai_reply = f"Bot reply to '{last_user_msg}' (Session context preserved)"
    return {"messages": [AIMessage(content=ai_reply)]}


def build_persistent_chat_graph():
    memory = MemorySaver()
    builder = StateGraph(ChatThreadState)
    builder.add_node("chatbot", chatbot_node)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)
    return builder.compile(checkpointer=memory)


def test_thread_conversational_persistence():
    graph = build_persistent_chat_graph()
    
    # Thread Config for User Session 42
    config_thread_42 = {"configurable": {"thread_id": "user_session_42"}}
    # Thread Config for User Session 99
    config_thread_99 = {"configurable": {"thread_id": "user_session_99"}}

    # Turn 1: User 42 asks a question
    res1 = graph.invoke({"messages": [HumanMessage(content="Hello, I am Hariom.")]}, config_thread_42)
    assert len(res1["messages"]) == 2  # Human + AI

    # Turn 2: User 42 asks follow-up (same thread_id)
    res2 = graph.invoke({"messages": [HumanMessage(content="What is my name?")]}, config_thread_42)
    # Checkpoint history preserves Turn 1 + Turn 2
    assert len(res2["messages"]) == 4  # (Human1 + AI1) + (Human2 + AI2)

    # Turn 1 for User 99 (different thread_id namespace)
    res3 = graph.invoke({"messages": [HumanMessage(content="Hello from User 99.")]}, config_thread_99)
    assert len(res3["messages"]) == 2  # Isolated namespace

    print("Concept 07 (Threads & Conversational Persistence) Passed Successfully!")
    print("User 42 Thread Messages Count:", len(res2["messages"]))
    print("User 99 Thread Messages Count:", len(res3["messages"]))


if __name__ == "__main__":
    test_thread_conversational_persistence()
