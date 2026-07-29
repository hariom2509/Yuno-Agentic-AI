"""
Concept 04: Command Primitive for State Update & Routing in LangGraph
Demonstrates:
1. Command(update={...}, goto=...) for combined atomic state mutation & node redirection
2. Cross-graph boundary control passing
"""

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph.message import add_messages


class CommandState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    target_skill: str


# Classifier Node returning a Command object
def intent_classifier_node(state: CommandState) -> Command:
    last_msg = state["messages"][-1].content.lower()

    if "code" in last_msg or "python" in last_msg:
        # Atomic state update + dynamic goto "coder_node"
        return Command(
            update={
                "current_agent": "Coder",
                "target_skill": "python_execution",
                "messages": [AIMessage(content="Routing request to Coding Agent...", name="Classifier")]
            },
            goto="coder_node"
        )
    else:
        # Atomic state update + dynamic goto "researcher_node"
        return Command(
            update={
                "current_agent": "Researcher",
                "target_skill": "web_search",
                "messages": [AIMessage(content="Routing request to Research Agent...", name="Classifier")]
            },
            goto="researcher_node"
        )


def coder_node(state: CommandState) -> dict:
    return {
        "messages": [AIMessage(content="Executing python code synthesis...", name="Coder")]
    }


def researcher_node(state: CommandState) -> dict:
    return {
        "messages": [AIMessage(content="Performing deep web search research...", name="Researcher")]
    }


def build_command_graph():
    builder = StateGraph(CommandState)

    builder.add_node("classifier", intent_classifier_node)
    builder.add_node("coder_node", coder_node)
    builder.add_node("researcher_node", researcher_node)

    builder.add_edge(START, "classifier")
    builder.add_edge("coder_node", END)
    builder.add_edge("researcher_node", END)

    return builder.compile()


def test_command_routing():
    graph = build_command_graph()

    # Case 1: Route to Coder
    res1 = graph.invoke({
        "messages": [HumanMessage(content="Write python code for binary search")],
        "current_agent": "Supervisor",
        "target_skill": "none"
    })

    assert res1["current_agent"] == "Coder"
    assert res1["target_skill"] == "python_execution"
    assert res1["messages"][-1].name == "Coder"
    print("Case 1 (Command -> Coder Node) Passed!")

    # Case 2: Route to Researcher
    res2 = graph.invoke({
        "messages": [HumanMessage(content="Analyze latest LLM enterprise benchmarks")],
        "current_agent": "Supervisor",
        "target_skill": "none"
    })

    assert res2["current_agent"] == "Researcher"
    assert res2["target_skill"] == "web_search"
    assert res2["messages"][-1].name == "Researcher"
    print("Case 2 (Command -> Researcher Node) Passed!")

    print("Concept 04 (Command for State Update & Routing) Passed Successfully!")


if __name__ == "__main__":
    test_command_routing()
