"""
LangGraph agent state definitions
"""

from typing import Annotated, List, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Central state object that flows through the LangGraph graph.
    Every node reads from and writes to this state.
    LangGraph persists this across cycles via MemorySaver checkpointer.
    """
    # Messages with add_messages reducer for LangGraph compatibility
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Current operation being performed
    current_operation: str
    
    # Result of the operation
    operation_result: str
    
    # List of extracted tasks
    extracted_tasks: List[dict]
    
    # Input text for processing
    input_text: str
    
    # Next action to take
    next_action: str
    
    # Cycle count for monitoring
    cycle_count: int
    
    # List of errors
    errors: List[str]
    
    # Daily summary
    daily_summary: str
