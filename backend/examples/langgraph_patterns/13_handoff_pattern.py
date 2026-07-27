"""
Concept 13: Handoff Multi-Agent Pattern
Demonstrates direct peer-to-peer agent control transfer (Agent A -> Agent B -> Agent C) without central supervisor bottleneck
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages

class HandoffState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    active_agent: str


# 1. Intake Agent Node -> Hands off directly to Triage Agent
def intake_agent_node(state: HandoffState) -> dict:
    return {
        "active_agent": "triage_agent",
        "messages": [AIMessage(content="Intake Agent: Request received. Handing off directly to Triage Agent.", name="IntakeAgent")]
    }


# 2. Triage Agent Node -> Hands off directly to Specialist Agent
def triage_agent_node(state: HandoffState) -> dict:
    return {
        "active_agent": "specialist_agent",
        "messages": [AIMessage(content="Triage Agent: Classified as technical issue. Handing off directly to Specialist Agent.", name="TriageAgent")]
    }


# 3. Specialist Agent Node -> Resolves and finishes
def specialist_agent_node(state: HandoffState) -> dict:
    return {
        "active_agent": "completed",
        "messages": [AIMessage(content="Specialist Agent: Technical issue resolved.", name="SpecialistAgent")]
    }


def build_handoff_graph():
    builder = StateGraph(HandoffState)

    builder.add_node("intake_agent", intake_agent_node)
    builder.add_node("triage_agent", triage_agent_node)
    builder.add_node("specialist_agent", specialist_agent_node)

    # Direct Peer-to-Peer Agent Handoff Pipeline
    builder.add_edge(START, "intake_agent")
    builder.add_edge("intake_agent", "triage_agent")
    builder.add_edge("triage_agent", "specialist_agent")
    builder.add_edge("specialist_agent", END)

    return builder.compile()


def test_handoff_pattern():
    graph = build_handoff_graph()

    res = graph.invoke({
        "messages": [HumanMessage(content="High latency incident on API Gateway")],
        "active_agent": "intake_agent"
    })

    assert res["active_agent"] == "completed"
    assert len(res["messages"]) == 4  # Human + Intake + Triage + Specialist
    assert res["messages"][-1].name == "SpecialistAgent"

    print("Concept 13 (Handoff Peer-to-Peer Agent Pattern) Passed Successfully!")
    print("Handoff Chain:")
    for m in res["messages"]:
        print(f" -> [{getattr(m, 'name', 'user')}] {m.content}")


if __name__ == "__main__":
    test_handoff_pattern()
