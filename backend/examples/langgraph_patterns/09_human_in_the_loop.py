"""
Concept 09: Human-in-the-Loop (HITL) with Interrupt for Dangerous MCP Tools
Demonstrates:
1. Automatic MCP Tool execution vs Dangerous MCP Tool execution requiring approval
2. Calling interrupt() to set state to WAITING_FOR_APPROVAL
3. Resuming graph execution with Command(resume="APPROVED" | "REJECTED")
"""

from typing import TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages
import operator

# List of dangerous MCP tools requiring human approval
DANGEROUS_MCP_TOOLS = {"mcp::github-mcp::delete_repository", "mcp::postgres-mcp::drop_table"}


class HITLState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    requested_tool: str
    tool_args: dict
    approval_status: str


def agent_decision_node(state: HITLState) -> dict:
    # Agent requests a dangerous MCP tool call
    return {
        "requested_tool": "mcp::github-mcp::delete_repository",
        "tool_args": {"repo": "hariom2509/temp_repo"},
        "messages": [AIMessage(content="Requesting tool execution: delete_repository")]
    }


def mcp_execution_node(state: HITLState) -> dict:
    tool_name = state["requested_tool"]

    # Security Layer 2: Check if invocation requires Human Approval (HITL Interrupt)
    if tool_name in DANGEROUS_MCP_TOOLS and state.get("approval_status") != "APPROVED":
        # Call LangGraph interrupt() primitive to pause execution and prompt human in UI
        human_response = interrupt({
            "status": "WAITING_FOR_APPROVAL",
            "message": f"Action Required: High-risk tool '{tool_name}' requires human approval.",
            "tool": tool_name,
            "args": state["tool_args"]
        })
        
        # When graph is resumed via Command(resume=...), human_response receives the payload
        if human_response != "APPROVED":
            return {
                "approval_status": "REJECTED",
                "messages": [AIMessage(content=f"Execution REJECTED by human supervisor for '{tool_name}'.")]
            }

    # Execute MCP tool after human approval
    return {
        "approval_status": "APPROVED",
        "messages": [AIMessage(content=f"Tool '{tool_name}' executed successfully after human approval.")]
    }


def build_hitl_mcp_graph(memory):
    builder = StateGraph(HITLState)
    builder.add_node("agent", agent_decision_node)
    builder.add_node("mcp_executor", mcp_execution_node)

    builder.add_edge(START, "agent")
    builder.add_edge("agent", "mcp_executor")
    builder.add_edge("mcp_executor", END)

    return builder.compile(checkpointer=memory)


def test_hitl_mcp_approval():
    memory = MemorySaver()
    graph = build_hitl_mcp_graph(memory)
    config = {"configurable": {"thread_id": "hitl_demo_session_1"}}

    # Step 1: Run graph until dangerous tool triggers interrupt()
    res1 = graph.invoke({"messages": [HumanMessage(content="Delete temporary repository")]}, config)
    
    # Verify graph is paused at interrupt point
    state_snapshot = graph.get_state(config)
    assert len(state_snapshot.tasks) > 0
    interrupt_data = state_snapshot.tasks[0].interrupts[0].value
    assert interrupt_data["status"] == "WAITING_FOR_APPROVAL"
    assert interrupt_data["tool"] == "mcp::github-mcp::delete_repository"
    print("Step 1: Graph successfully paused on interrupt() -> WAITING_FOR_APPROVAL!")

    # Step 2: Human Approves action via Command(resume="APPROVED")
    res_approved = graph.invoke(Command(resume="APPROVED"), config)
    assert res_approved["approval_status"] == "APPROVED"
    assert "executed successfully after human approval" in res_approved["messages"][-1].content
    print("Step 2: Graph resumed with Command(resume='APPROVED')!")

    print("Concept 09 (Human-in-the-Loop Interrupt & Approval) Passed Successfully!")


if __name__ == "__main__":
    test_hitl_mcp_approval()
