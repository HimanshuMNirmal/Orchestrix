"""
Agent runner for managing LangGraph execution
"""

import threading
import time
from langchain_core.messages import HumanMessage, AIMessage

from models.memory_store import MemoryStore
from models.agent_state import AgentState
from .builder import build_agent_graph
from .tools import set_global_memory


class AgentRunner:
    """
    Manages the LangGraph agent execution.
    Runs the graph in a background thread with a persistent thread_id.
    """

    def __init__(self, memory_store: MemoryStore, ui_callback=None, integration_mode="mock"):
        self.memory = memory_store
        self.ui_callback = ui_callback
        self.integration_mode = integration_mode
        self._running = False
        self._thread = None
        self._thread_id = "desktop-agent-os-main"  # Persistent ID for checkpointing

        set_global_memory(memory_store, ui_callback, integration_mode)

        self.graph, self.nodes = build_agent_graph(memory_store, integration_mode=integration_mode)
        self._config = {"configurable": {"thread_id": self._thread_id}}

    def emit(self, msg: str, level: str = "info"):
        if self.ui_callback:
            self.ui_callback(msg, level)

    def _get_initial_state(self) -> dict:
        return {
            "messages": [],
            "current_operation": "idle",
            "operation_result": "",
            "extracted_tasks": [],
            "input_text": "",
            "next_action": "monitor",
            "cycle_count": 0,
            "errors": [],
            "daily_summary": "",
        }

    def run_monitor_cycle(self):
        """Run a single monitoring cycle through the graph"""
        try:
            state = {
                **self._get_initial_state(),
                "next_action": "monitor",
            }
            for event in self.graph.stream(state, self._config):
                node_name = list(event.keys())[0]
                self.emit(f"  ↳ Node: {node_name}", "info")
        except Exception as e:
            self.emit(f"❌ Graph error: {e}", "error")

    def run_extract_cycle(self, text: str):
        """Run a task extraction cycle through the graph"""
        try:
            state = {
                **self._get_initial_state(),
                "input_text": text,
                "next_action": "extract",
            }
            for event in self.graph.stream(state, self._config):
                node_name = list(event.keys())[0]
                self.emit(f"  ↳ Node: {node_name}", "info")
        except Exception as e:
            self.emit(f"❌ Extraction error: {e}", "error")

    def run_chat(self, user_message: str) -> str:
        """Run a chat interaction through the graph and return response"""
        try:
            state = {
                **self._get_initial_state(),
                "messages": [HumanMessage(content=user_message)],
                "next_action": "chat",
            }
            final_state = None
            for event in self.graph.stream(state, self._config):
                final_state = event

            # Extract the last AI message as the response
            if final_state:
                last_node_state = list(final_state.values())[0]
                messages = last_node_state.get("messages", [])
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        return str(msg.content)
            return "I processed your request but couldn't generate a response."
        except Exception as e:
            return f"Error: {str(e)}"

    def start_loop(self):
        """Start continuous monitoring loop in background thread"""
        if self._running:
            return
        self._running = True
        self.memory.agent_running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.emit("🚀 LangGraph agent started", "success")

    def stop_loop(self):
        self._running = False
        self.memory.agent_running = False
        self.emit("⏹️ Agent stopped", "info")

    def _loop(self):
        """Background monitoring loop — runs every 30 seconds"""
        iteration = 0
        while self._running:
            iteration += 1
            self.emit(f"\n🔄 Monitoring cycle #{iteration}", "info")
            self.run_monitor_cycle()
            self.emit("✅ Cycle complete. Next in 30s...", "success")
            for _ in range(30):
                if not self._running:
                    break
                time.sleep(1)
