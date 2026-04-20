"""
LangGraph node functions for the agent
"""

import json
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END

from models.memory_store import MemoryStore
from models.agent_state import AgentState
from .tools import AGENT_TOOLS, emit


class AgentNodes:
    """
    All LangGraph node functions.
    Each node takes AgentState → returns partial AgentState update.
    Nodes are connected into a graph with conditional edges.
    """

    def __init__(self, memory_store: MemoryStore, integration_mode="mock"):
        self.memory = memory_store
        self.integration_mode = integration_mode

        # LLM with tools bound — this enables automatic tool calling
        # Using local Ollama model (Llama 3.2 3B) - completely free
        self.llm = ChatOllama(
            model="llama3.2:3b",
            base_url="http://localhost:11434",
            temperature=0.7,
            max_tokens=2000,
            streaming=True
        )
        self.llm_with_tools = self.llm.bind_tools(AGENT_TOOLS)

    # ── Node 1: Intake ──────────────────────────────────────────────────────
    def intake_node(self, state: AgentState) -> dict:
        """
        INTAKE NODE
        Entry point for every agent cycle.
        Reads current system state and decides what operation to run next.

        Routes to:
          - "extract"   if there's input_text to process
          - "monitor"   for a normal monitoring cycle
          - "chat"      if the last message is a user chat message
        """
        emit("🔵 [Intake] Analyzing current state...", "info")

        snapshot = self.memory.snapshot()
        last_messages = state.get("messages", [])
        input_text = state.get("input_text", "")
        cycle = state.get("cycle_count", 0)

        # Determine next action based on context
        if input_text and input_text.strip():
            next_action = "extract"
        elif last_messages and isinstance(last_messages[-1], HumanMessage):
            next_action = "chat"
        else:
            next_action = "monitor"

        system_msg = SystemMessage(content=f"""You are the Desktop Agent OS — an intelligent work automation agent.

Current system snapshot:
{json.dumps(snapshot, indent=2)}

Cycle #{cycle+1} | Next action: {next_action}

Your job:
- Monitor tasks, detect overdue items, generate follow-ups
- Extract tasks from user-provided text
- Answer user questions about their workload
- Use available tools to take action""")

        return {
            "next_action": next_action,
            "current_operation": "intake",
            "cycle_count": cycle + 1,
            "messages": [system_msg],
            "errors": [],
        }

    # ── Node 2: Extract Tasks ────────────────────────────────────────────────
    def extract_node(self, state: AgentState) -> dict:
        """
        EXTRACT NODE
        Uses LLM + tools to extract structured tasks from raw text.
        The LLM reads the text, identifies action items, calls extract_and_save_tasks tool.
        """
        emit("🟣 [Extract] Extracting tasks from input text...", "info")
        input_text = state.get("input_text", "")
        
        # Prevent infinite loops - filter out system prompts and empty text
        if not input_text or len(input_text.strip()) < 10:
            emit("⚠️ Input text too short or empty, skipping extraction", "warning")
            return {
                "current_operation": "extract",
                "operation_result": "No valid text to extract from",
                "input_text": "",  # Clear after processing
                "next_action": END,
            }
        
        # Check if input looks like a system prompt (contains tool instructions)
        suspicious_keywords = ["extract_and_save_tasks", "call the", "tool to save it", "Be specific about task titles"]
        if any(keyword in input_text for keyword in suspicious_keywords):
            emit("⚠️ System prompt detected in input, skipping extraction", "warning")
            return {
                "current_operation": "extract",
                "operation_result": "System prompt detected, skipping extraction",
                "input_text": "",  # Clear after processing
                "next_action": END,
            }

        prompt = HumanMessage(content=f"""Extract all actionable tasks from the following text.
For each task you identify, call the extract_and_save_tasks tool to save it.
Be specific about task titles. Identify owners if mentioned.

Text to analyze:
---
{input_text}
---

After saving all tasks, call log_agent_activity with a summary of what you found.""")

        response = self.llm_with_tools.invoke(state["messages"] + [prompt])

        return {
            "messages": [prompt, response],
            "current_operation": "extract",
            "operation_result": response.content if isinstance(response.content, str) else "Tasks extracted",
            "input_text": "",  # Clear after processing
            "next_action": "tools" if (hasattr(response, 'tool_calls') and response.tool_calls) else "summarize",
        }

    # ── Node 3: Monitor ──────────────────────────────────────────────────────
    def monitor_node(self, state: AgentState) -> dict:
        """
        MONITOR NODE
        Core agent monitoring cycle. The LLM:
        1. Reads current task snapshot
        2. Calls flag_overdue_tasks
        3. Calls generate_followup_reminders
        4. Assesses risks and logs activity
        """
        emit("🟡 [Monitor] Running monitoring cycle...", "info")

        prompt = HumanMessage(content="""Run a full monitoring cycle:
1. Call get_task_summary to understand current state
2. Call flag_overdue_tasks to mark any overdue items
3. Call generate_followup_reminders for stale tasks
4. Call log_agent_activity with a brief summary of what you found and any actions taken

Be thorough but concise.""")

        response = self.llm_with_tools.invoke(state["messages"] + [prompt])

        return {
            "messages": [prompt, response],
            "current_operation": "monitor",
            "operation_result": response.content if isinstance(response.content, str) else "Monitoring complete",
            "next_action": "tools" if (hasattr(response, 'tool_calls') and response.tool_calls) else "summarize",
        }

    # ── Node 4: Chat ─────────────────────────────────────────────────────────
    def chat_node(self, state: AgentState) -> dict:
        """
        CHAT NODE
        Handles conversational user queries.
        The LLM can use tools to answer questions about tasks, priorities, etc.
        """
        emit("🟢 [Chat] Processing user message...", "info")

        try:
            # Get the last human message for context
            messages = state["messages"]
            user_message = ""
            for msg in reversed(messages):
                # Only get human messages, not system messages or AI messages
                if hasattr(msg, 'type') and msg.type == 'human':
                    user_message = msg.content
                    break
                # Fallback: check if it's not a system/AI/tool message
                elif hasattr(msg, 'content') and not hasattr(msg, 'tool_calls') and not hasattr(msg, 'type') or msg.type not in ['system', 'ai', 'tool']:
                    # Check if content looks like user input (shorter, no JSON)
                    content = msg.content
                    if content and len(content) < 200 and '{' not in content and 'system snapshot' not in content.lower():
                        user_message = content
                        break
            
            # Debug logging
            emit(f"🔍 Chat Debug: User message = '{user_message}'", "info")
            
            # Use LLM to determine user intent and extract filters
            try:
                intent_prompt = f"""Analyze the user's message and determine their intent and any filters. Respond in this JSON format:

{{
  "intent": "CREATE_TASK|UPDATE_TASK|MANAGE_TASK|VIEW_TASKS|SHOW_TOOLS|GENERAL_CHAT",
  "filters": {{
    "priority": "critical|high|medium|low|",
    "status": "pending|in_progress|completed|overdue|",
    "owner": "person_name|",
    "search": "search_terms|"
  }}
}}

Examples:
- "what are the tasks with medium priority" -> {{"intent": "VIEW_TASKS", "filters": {{"priority": "medium"}}}}
- "show me overdue tasks for john" -> {{"intent": "VIEW_TASKS", "filters": {{"status": "overdue", "owner": "john"}}}}
- "create high priority task" -> {{"intent": "CREATE_TASK", "filters": {{"priority": "high"}}}}

User message: {user_message}

Response:"""
                
                from langchain_core.messages import HumanMessage, SystemMessage
                system_msg = SystemMessage(content="You are an intent classifier. Respond with only the exact intent command.")
                human_msg = HumanMessage(content=intent_prompt)
                
                intent_response = self.llm.invoke([system_msg, human_msg])
                
                # Parse JSON response
                try:
                    import json
                    intent_data = json.loads(intent_response.content.strip())
                    intent = intent_data.get('intent', 'GENERAL_CHAT')
                    filters = intent_data.get('filters', {})
                except:
                    # Fallback if JSON parsing fails
                    intent = intent_response.content.strip().upper()
                    filters = {}
                
                emit(f" Chat Debug: LLM detected intent = '{intent}', filters = {filters}", "info")
                
                # Route based on LLM-determined intent
                if intent == "CREATE_TASK":
                    emit(" Chat Debug: Routing to CREATE_TASK", "info")
                    
                    # Check if user provided task details
                    if len(user_message.strip()) > 10:  # Has some content
                        try:
                            # Create a prompt for the LLM to extract structured task information
                            task_prompt = f"""Extract a structured task from the following user request:

User request: {user_message}

Please analyze this request and provide a clean task description in this format:

TITLE: [Clear, concise title max 80 chars]
DESCRIPTION: [Detailed description of what needs to be done]
PRIORITY: [critical/high/medium/low]
DEADLINE: [Any mentioned deadline or 'none']
OWNER: [Any mentioned person or 'unassigned']

Focus on the actual task, not the words "create task". Use 'medium' priority if not specified. Use 'none' for deadline if not mentioned. Use 'unassigned' for owner if not mentioned. Do NOT use markdown formatting or asterisks."""
                            
                            task_system_msg = SystemMessage(content="You are a task extraction assistant. Extract clear, actionable tasks from user requests.")
                            task_human_msg = HumanMessage(content=task_prompt)
                            
                            task_llm_response = self.llm.invoke([task_system_msg, task_human_msg])
                            
                            # Parse the structured response to extract all task fields
                            response_lines = task_llm_response.content.strip().split('\n')
                            task_title = ""
                            task_description = ""
                            task_priority = "medium"
                            task_deadline = ""
                            task_owner = "unassigned"
                            
                            for line in response_lines:
                                if line.startswith('TITLE:'):
                                    task_title = line.replace('TITLE:', '').strip()
                                elif line.startswith('DESCRIPTION:'):
                                    task_description = line.replace('DESCRIPTION:', '').strip()
                                elif line.startswith('PRIORITY:'):
                                    task_priority = line.replace('PRIORITY:', '').strip()
                                elif line.startswith('DEADLINE:'):
                                    task_deadline = line.replace('DEADLINE:', '').strip()
                                elif line.startswith('OWNER:'):
                                    task_owner = line.replace('OWNER:', '').strip()
                            
                            # Create a comprehensive task description with all details
                            full_task_description = task_title
                            if task_description:
                                full_task_description += f"\n\n{task_description}"
                            if task_owner != "unassigned":
                                full_task_description += f"\n\nAssigned to: {task_owner}"
                            if task_priority != "medium":
                                full_task_description += f"\n\nPriority: {task_priority}"
                            if task_deadline != "none":
                                full_task_description += f"\n\nDeadline: {task_deadline}"
                            
                            # Use the comprehensive description for task creation
                            if task_title:
                                from .tools import extract_and_save_tasks
                                result = extract_and_save_tasks.func(text=full_task_description, source="manual")
                                
                                from langchain_core.messages import AIMessage
                                response = AIMessage(content=f"✅ Task created successfully!\n\n{result}\n\n📝 **Extracted details:**\n{task_llm_response.content}")
                            else:
                                # Fallback if parsing fails
                                from .tools import extract_and_save_tasks
                                result = extract_and_save_tasks.func(text=user_message, source="manual")
                                
                                from langchain_core.messages import AIMessage
                                response = AIMessage(content=f"✅ Task created successfully!\n\n{result}")
                        except Exception as e:
                            emit(f"Task creation error: {e}", "error")
                            from langchain_core.messages import AIMessage
                            response = AIMessage(content=f"I had trouble creating the task: {e}\n\nPlease try again with a clearer task description.")
                    else:
                        # Show guidance for task creation
                        from langchain_core.messages import AIMessage
                        response = AIMessage(content="To create a task, please provide the task details. For example:\n\n'Create task: Review the quarterly report by Friday'\n\nOr just tell me what you need to do and I'll extract it as a task.")
                        
                elif intent == "UPDATE_TASK":
                    emit(" Chat Debug: Routing to UPDATE_TASK", "info")
                    from langchain_core.messages import AIMessage
                    response = AIMessage(content="To update a task, I need the task ID and new status. For example:\n\n'Mark task abc12345 as completed'\n\nFirst ask 'what are my tasks?' to see task IDs.")
                    
                elif intent == "MANAGE_TASK":
                    emit(" Chat Debug: Routing to MANAGE_TASK", "info")
                    # Route to manage_task_node by setting next_action
                    manage_prompt = HumanMessage(content=f"Process this task management request: {user_message}")
                    
                    return {
                        "messages": [manage_prompt],
                        "current_operation": "manage_task",
                        "operation_result": "Task management request received",
                        "next_action": "manage_task",
                    }
                    
                elif intent == "VIEW_TASKS":
                    emit("🔍 Chat Debug: Routing to VIEW_TASKS", "info")
                    from .tools import get_task_summary
                    task_info = get_task_summary.func(**filters) if filters else get_task_summary.func()
                    
                    filter_desc = ""
                    if filters:
                        filter_parts = []
                        if filters.get('priority'):
                            filter_parts.append(f"priority: {filters['priority']}")
                        if filters.get('status'):
                            filter_parts.append(f"status: {filters['status']}")
                        if filters.get('owner'):
                            filter_parts.append(f"owner: {filters['owner']}")
                        if filters.get('search'):
                            filter_parts.append(f"search: {filters['search']}")
                        if filter_parts:
                            filter_desc = f" (filtered by {', '.join(filter_parts)})"
                    
                    from langchain_core.messages import AIMessage
                    response = AIMessage(content=f"Here are your current tasks{filter_desc}:\n{task_info}")
                    
                elif intent == "SHOW_TOOLS":
                    emit("🔍 Chat Debug: Routing to SHOW_TOOLS", "info")
                    from .tools import list_available_tools
                    tools_info = list_available_tools.func()
                    
                    from langchain_core.messages import AIMessage
                    response = AIMessage(content=f"Here are all available tools:\n{tools_info}")
                    
                else:  # GENERAL_CHAT or anything else
                    emit("🔍 Chat Debug: Routing to GENERAL_CHAT", "info")
                    response = self.llm_with_tools.invoke(messages)
                    
            except Exception as e:
                emit(f"Intent detection error: {e}, using fallback", "error")
                response = self.llm_with_tools.invoke(messages)
        except Exception as e:
            emit(f"Chat error: {e}", "error")
            from langchain_core.messages import AIMessage
            response = AIMessage(content="I'm having trouble processing your request. Please try again.")

        return {
            "messages": [response],
            "current_operation": "chat",
            "operation_result": response.content if isinstance(response.content, str) else "",
            "next_action": "tools" if (hasattr(response, 'tool_calls') and response.tool_calls) else END,
        }

    # Task Management Node
    def manage_task_node(self, state: AgentState) -> dict:
        """
        MANAGE TASK NODE
        Handles task management operations like assigning tasks, updating deadlines, changing priorities.
        This node processes user requests to modify existing tasks.
        """
        emit("  Manage Task: Processing task management request...", "info")
        
        messages = state["messages"]
        # Get the last human message for task management context
        user_message = ""
        for msg in reversed(messages):
            if hasattr(msg, 'type') and msg.type == 'human':
                user_message = msg.content
                break
        
        prompt = HumanMessage(content=f"""Process this task management request:
        
User request: {user_message}

You MUST use the available tools to complete this request. Do not just provide a response - take action.

Available tools:
- update_task_status: Update task status, risk level, owner, deadline, or priority
- get_task_summary: Get current task information to identify tasks

Required workflow:
1. First, call get_task_summary to see current tasks and verify the task ID exists
2. Then, call update_task_status with the specific task ID and requested changes
3. Finally, call log_agent_activity with a summary of what was updated

For this request: "{user_message}"
Extract the task ID and what needs to be changed, then use the tools to make it happen.

Example:
- If user says "change priority of task abc12345 to high", call: update_task_status(task_id="abc12345", priority="high")
- If user says "assign task xyz67890 to john@email.com", call: update_task_status(task_id="xyz67890", owner="john@email.com")

IMPORTANT: You MUST call the tools, not just describe what you would do.""")
        
        response = self.llm_with_tools.invoke(state["messages"] + [prompt])
        
        # Debug: Log what the LLM returned
        emit(f" Manage Task Debug: Response type = {type(response)}", "info")
        emit(f" Manage Task Debug: Has tool calls = {hasattr(response, 'tool_calls')}", "info")
        if hasattr(response, 'tool_calls') and response.tool_calls:
            emit(f" Manage Task Debug: Tool calls = {response.tool_calls}", "info")
        else:
            emit(f" Manage Task Debug: Content = {response.content[:200]}", "info")
        
        return {
            "messages": [prompt, response],
            "current_operation": "manage_task",
            "operation_result": response.content if isinstance(response.content, str) else "Task management complete",
            "next_action": "tools" if (hasattr(response, 'tool_calls') and response.tool_calls) else END,
        }

    # ── Node 5: Tools ────────────────────────────────────────────────────────
    def tools_node(self, state: AgentState) -> dict:
        """
        TOOLS NODE
        Executes tool calls made by the LLM.
        LangGraph automatically handles tool call → tool result routing.

        This is a manual tools node to give us visibility into what tools are running.
        In production you can use langgraph.prebuilt.ToolNode instead.
        """
        from langchain_core.messages import ToolMessage

        messages = state["messages"]
        last_message = messages[-1]
        tool_results = []

        tool_map = {t.name: t for t in AGENT_TOOLS}

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            emit(f"🔧 [Tool] Running: {tool_name}({tool_args})", "info")

            try:
                tool_fn = tool_map.get(tool_name)
                if tool_fn:
                    result = tool_fn.invoke(tool_args)
                else:
                    result = f"Tool '{tool_name}' not found"
            except Exception as e:
                result = f"Tool error: {str(e)}"
                emit(f"❌ Tool error in {tool_name}: {e}", "error")

            tool_results.append(
                ToolMessage(content=str(result), tool_call_id=tool_id)
            )

        return {
            "messages": tool_results,
            "next_action": "continue",
        }

    # ── Node 6: Summarize ────────────────────────────────────────────────────
    def summarize_node(self, state: AgentState) -> dict:
        """
        SUMMARIZE NODE
        Generates a concise daily summary after a monitoring cycle.
        Only runs periodically (every 5 cycles).
        """
        cycle = state.get("cycle_count", 0)
        if cycle % 5 != 0:
            return {"next_action": END}

        emit("📋 [Summarize] Generating daily summary...", "info")

        snapshot = self.memory.snapshot()
        prompt = HumanMessage(content=f"""Generate a concise daily work summary.

Current data:
{json.dumps(snapshot, indent=2)}

Include:
1. Executive summary (2-3 sentences)
2. Critical items needing immediate attention
3. Deadlines in next 48 hours
4. Top recommendations

Keep it professional and under 300 words.""")

        response = self.llm.invoke(state["messages"] + [prompt])
        summary = response.content if isinstance(response.content, str) else ""

        if self.memory:
            self.memory.log_activity("summary_generated", "agent", "Daily summary generated")

        emit("✅ Daily summary ready", "success")

        return {
            "messages": [prompt, response],
            "daily_summary": summary,
            "current_operation": "summarize",
            "next_action": END,
        }


# ── Router Functions ──────────────────────────────────────────────────────────

def route_from_intake(state: AgentState) -> Literal["extract", "monitor", "chat", "manage_task"]:
    """Routes from intake node based on next_action"""
    action = state.get("next_action", "monitor")
    if action == "extract":
        return "extract"
    elif action == "chat":
        return "chat"
    elif action == "manage_task":
        return "manage_task"
    return "monitor"


def route_after_llm(state: AgentState) -> Literal["tools", "summarize", "__end__"]:
    """Routes after any LLM node — go to tools if tool calls exist, else summarize or end"""
    next_action = state.get("next_action", END)
    if next_action == "tools":
        return "tools"
    elif next_action == "summarize":
        return "summarize"
    return END


def route_after_tools(state: AgentState) -> Literal["monitor", "chat", "extract", "summarize", "manage_task", "__end__"]:
    """After tools run, route appropriately - monitor cycles should end after tools"""
    operation = state.get("current_operation", "monitor")
    if operation == "extract":
        return "extract"
    elif operation == "chat":
        return "chat"
    elif operation == "manage_task":
        return END  # End after task management
    elif operation == "monitor":
        # For monitoring cycles, go to summarize after tools to end the cycle
        return "summarize"
    return END
