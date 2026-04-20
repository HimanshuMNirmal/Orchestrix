"""
LangGraph graph builder for Desktop Agent OS
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.memory_store import MemoryStore
from models.agent_state import AgentState
from .nodes import AgentNodes, route_from_intake, route_after_llm, route_after_tools


def build_agent_graph(memory_store: MemoryStore, integration_mode="mock") -> tuple:
    """
    Constructs and compiles the LangGraph StateGraph.

    Graph topology:
    
    [START] → intake
                ├─ "extract" → extract → tools? → extract (loop) → summarize → END
                ├─ "monitor" → monitor → tools? → monitor (loop) → summarize → END
                └─ "chat"   → chat    → tools? → chat    (loop)             → END

    MemorySaver checkpointer enables persistence across runs.
    """
    nodes = AgentNodes(memory_store, integration_mode=integration_mode)
    checkpointer = MemorySaver()

    # Create graph with AgentState schema
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("intake", nodes.intake_node)
    graph.add_node("extract", nodes.extract_node)
    graph.add_node("monitor", nodes.monitor_node)
    graph.add_node("chat", nodes.chat_node)
    graph.add_node("manage_task", nodes.manage_task_node)
    graph.add_node("tools", nodes.tools_node)
    graph.add_node("summarize", nodes.summarize_node)

    # Entry point
    graph.set_entry_point("intake")

    # Intake → branch
    graph.add_conditional_edges(
        "intake",
        route_from_intake,
        {"extract": "extract", "monitor": "monitor", "chat": "chat", "manage_task": "manage_task"}
    )

    # Each LLM node → tools or summarize or end
    for llm_node in ["extract", "monitor", "chat", "manage_task"]:
        graph.add_conditional_edges(
            llm_node,
            route_after_llm,
            {"tools": "tools", "summarize": "summarize", END: END}
        )

    # Tools → back to originating LLM node or summarize
    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {"extract": "extract", "monitor": "summarize", "chat": "chat", "manage_task": END, "summarize": "summarize", END: END}
    )

    # Summarize always ends
    graph.add_edge("summarize", END)

    # Compile with memory checkpointer for state persistence
    compiled = graph.compile(checkpointer=checkpointer)
    return compiled, nodes
