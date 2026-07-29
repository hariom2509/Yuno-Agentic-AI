"""
Concept 03: Tool-Calling Loops in LangGraph
Demonstrates:
1. Custom ToolNode implementation & conditional tool router
2. Dynamic MCP Tool Dispatching Loop
"""

from typing import TypedDict, Annotated, List, Callable, Any, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
import json


# Define a sample tool function
def calculate_tax_func(amount: float) -> str:
    """Calculates 10% tax on an amount."""
    return json.dumps({"amount": amount, "tax": amount * 0.10})


class ToolLoopState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


# Production ToolNode Abstraction
class ProductionToolNode:
    def __init__(self, tools: List[Callable]):
        self.tools_by_name = {t.__name__: t for t in tools}

    def __call__(self, state: ToolLoopState) -> dict:
        last_msg = state["messages"][-1]
        tool_calls = getattr(last_msg, "tool_calls", [])
        results = []

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            call_id = call.get("id", "call_001")

            if tool_name in self.tools_by_name:
                output = self.tools_by_name[tool_name](**tool_args)
            else:
                output = f"Tool '{tool_name}' not found."

            results.append(
                ToolMessage(content=str(output), tool_call_id=call_id, name=tool_name)
            )

        return {"messages": results}


# Standard tools_condition router
def tools_condition(state: ToolLoopState) -> str:
    """Inspects the last message for tool_calls."""
    last_msg = state["messages"][-1]
    if isinstance(last_msg, AIMessage) and getattr(last_msg, "tool_calls", None):
        return "tools"
    return END


# Simulated Agent Node emitting tool calls
def mock_agent_node(state: ToolLoopState) -> dict:
    msgs = state["messages"]
    last_msg = msgs[-1]

    # If the last message was a ToolMessage, synthesize final answer
    if isinstance(last_msg, ToolMessage):
        return {
            "messages": [AIMessage(content=f"Final Answer based on tool output: {last_msg.content}")]
        }
    
    # Emit an AIMessage with a tool_call
    return {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "calculate_tax_func",
                    "args": {"amount": 500.0},
                    "id": "call_tax_001"
                }]
            )
        ]
    }


def build_tool_loop_graph():
    builder = StateGraph(ToolLoopState)
    tool_node = ProductionToolNode([calculate_tax_func])

    builder.add_node("agent", mock_agent_node)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "agent")
    
    # Conditional routing: if agent emits tool_calls -> route to "tools", else -> END
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")

    return builder.compile()


def test_tool_loops():
    graph = build_tool_loop_graph()
    res = graph.invoke({"messages": [HumanMessage(content="Calculate tax for 500")]})
    
    assert len(res["messages"]) == 4  # HumanMessage + AIMessage (tool_call) + ToolMessage + AIMessage (final)
    assert isinstance(res["messages"][-1], AIMessage)
    assert "Final Answer based on tool output" in res["messages"][-1].content

    print("Concept 03 (Tool-Calling Loops & ToolNode Abstraction) Passed Successfully!")
    print("Execution Trace:")
    for m in res["messages"]:
        print(f" - [{m.type.upper()}] {getattr(m, 'name', 'Agent')}: {m.content[:80]}")


if __name__ == "__main__":
    test_tool_loops()
