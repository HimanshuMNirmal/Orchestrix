"""
LangGraph tools for the agent
"""

import json
import datetime
from typing import Optional
from langchain_core.tools import tool

from models.task import Task
from models.memory_store import MemoryStore


# Global references for tools
_memory_store: Optional[MemoryStore] = None
_ui_callback = None
_integration_mode = "mock"


def set_global_memory(store: MemoryStore, callback=None, integration_mode="mock"):
    """Set global memory store and UI callback for tools"""
    global _memory_store, _ui_callback, _integration_mode
    _memory_store = store
    _ui_callback = callback
    _integration_mode = integration_mode


def emit(msg: str, level: str = "info"):
    """Emit message to UI callback if available"""
    if _ui_callback:
        _ui_callback(msg, level)


@tool
def extract_and_save_tasks(text: str, source: str = "manual") -> str:
    """
    Extract actionable tasks from unstructured text and save them to memory.
    Use this when the user provides text (email, Slack message, meeting notes)
    and wants tasks extracted from it.

    Args:
        text: The raw text to extract tasks from
        source: Where the text came from (slack, gmail, notion, jira, manual)

    Returns:
        A summary of tasks that were extracted and saved
    """
    if not _memory_store:
        return "Memory store not initialized"
    
    # Prevent processing system prompts or tool instructions
    suspicious_keywords = ["extract_and_save_tasks", "call the", "tool to save it", "Be specific about task titles", "For each task you identify"]
    if any(keyword in text for keyword in suspicious_keywords):
        emit("⚠️ Tool instruction detected, not creating task", "warning")
        return "Detected tool instruction text, not creating a task"
    
    # Skip empty or very short text
    if not text or len(text.strip()) < 10:
        emit("⚠️ Text too short, not creating task", "warning")
        return "Text too short to create a meaningful task"

    # Parse structured task data from LLM response
    # Extract owner, priority, and other details from the description
    owner = "unassigned"
    priority = "medium"
    
    # Extract owner from description
    if "Assigned to:" in text:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Assigned to:'):
                owner = line.replace('Assigned to:', '').strip()
                break
    elif "Owner:" in text:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Owner:'):
                owner = line.replace('Owner:', '').strip()
                break
    
    # Extract priority from description
    if "Priority:" in text:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Priority:'):
                priority = line.replace('Priority:', '').strip().lower()
                break
    
    # Get the title (first line or first 80 chars)
    lines = text.split('\n')
    title = lines[0] if lines else text[:80]
    if len(title) > 80:
        title = title[:80]
    
    # Create task with extracted information
    task = Task(
        title=title,
        description=text,
        source=source,
        priority=priority,
        owner=owner
    )
    task_id = _memory_store.add_task(task)
    emit(f"✅ Task saved: {task.title}", "success")
    return f"Saved task '{task.title}' with ID {task_id}"


@tool
def get_task_summary(priority: str = None, status: str = None, owner: str = None, search: str = None) -> str:
    """
    Get a current summary of tasks with optional filtering.
    Use this to understand the current workload before making decisions.

    Args:
        priority: Filter by priority level (critical, high, medium, low)
        status: Filter by status (pending, in_progress, completed, overdue)
        owner: Filter by owner name
        search: Filter by search terms in title/description

    Returns:
        Human-readable summary of tasks and statistics
    """
    if not _memory_store:
        return "Memory store not initialized"
    snapshot = _memory_store.snapshot()
    
    # Apply filters
    tasks = snapshot.get('tasks', [])
    original_count = len(tasks)
    
    if priority:
        tasks = [task for task in tasks if task.get('priority', '').lower() == priority.lower()]
    if status:
        if status == 'overdue':
            tasks = [task for task in tasks if task.get('is_overdue', False)]
        else:
            tasks = [task for task in tasks if task.get('status', '').lower() == status.lower()]
    if owner:
        tasks = [task for task in tasks if owner.lower() in task.get('owner', '').lower()]
    if search:
        search_lower = search.lower()
        tasks = [task for task in tasks if search_lower in task.get('title', '').lower() or search_lower in task.get('description', '').lower()]
    
    # Recalculate counts for filtered tasks
    filtered_count = len(tasks)
    overdue_count = len([task for task in tasks if task.get('is_overdue', False)])
    stale_count = 0  # Would need date calculation for this
    
    # Format as human-readable text instead of JSON
    total_tasks = filtered_count
    
    if total_tasks == 0:
        return "You currently have no tasks. Your task list is empty!"
    
    summary_lines = [
        f"📊 **Task Summary ({total_tasks} total tasks)**",
        f"",
        f"⚠️ Overdue: {overdue_count}",
        f"🕐 Stale (48h+): {stale_count}",
        f""
    ]
    
    if tasks:
        summary_lines.append("📋 **Current Tasks:**")
        for i, task in enumerate(tasks[:20], 1):  # Show max 20 tasks
            status_emoji = "🟡" if task.get('status') == 'pending' else "🔵" if task.get('status') == 'in_progress' else "🟢" if task.get('status') == 'completed' else "🔴"
            priority_emoji = "🔴" if task.get('priority') == 'critical' else "🟠" if task.get('priority') == 'high' else "🟡" if task.get('priority') == 'medium' else "🟢"
            title = task.get('title', 'Untitled')
            owner = task.get('owner', 'Unassigned')
            summary_lines.append(f"{i}. {status_emoji} {priority_emoji} {title} (Owner: {owner})")
        
        if len(tasks) > 20:
            summary_lines.append(f"... and {len(tasks) - 20} more tasks")
        elif len(tasks) > 10:
            summary_lines.append(f"Showing all {len(tasks)} tasks")
    
    return "\n".join(summary_lines)


@tool
def update_task_status(task_id: str, status: str = None, risk_level: str = None, owner: str = None, deadline: str = None, priority: str = None) -> str:
    """
    Update multiple fields of an existing task.

    Args:
        task_id: The 8-character task ID
        status: Optional new status -- one of: pending, in_progress, completed, overdue
        risk_level: Optional new risk level -- one of: low, medium, high, critical
        owner: Optional new owner email address
        deadline: Optional new deadline in YYYY-MM-DD format
        priority: Optional new priority -- one of: low, medium, high, critical

    Returns:
        Confirmation message with all changes made
    """
    if not _memory_store:
        return "Memory store not initialized"
    
    updates = {}
    changes = []
    
    if status:
        updates["status"] = status
        changes.append(f"status to '{status}'")
    if risk_level:
        updates["risk_level"] = risk_level
        changes.append(f"risk level to '{risk_level}'")
    if owner:
        updates["owner"] = owner
        changes.append(f"owner to '{owner}'")
    if deadline:
        updates["deadline"] = deadline
        changes.append(f"deadline to '{deadline}'")
    if priority:
        updates["priority"] = priority
        changes.append(f"priority to '{priority}'")
    
    if not updates:
        return "No updates specified - please provide at least one field to update"
    
    success = _memory_store.update_task(task_id, **updates)
    if success:
        change_desc = ", ".join(changes)
        emit(f" Task {task_id} updated: {change_desc}", "info")
        return f"Task {task_id} updated: {change_desc}"
    return f"Task {task_id} not found"


@tool
def flag_overdue_tasks() -> str:
    """
    Scan all tasks and flag any that are past their deadline.
    Updates their status to 'overdue' and risk_level to 'high' or 'critical'.

    Returns:
        Summary of tasks that were flagged
    """
    if not _memory_store:
        return "Memory store not initialized"
    overdue = _memory_store.get_overdue_tasks()
    flagged = []
    for task in overdue:
        _memory_store.update_task(task.id, status="overdue", risk_level="critical")
        flagged.append(task.title)
        emit(f"🚨 Overdue flagged: {task.title}", "error")
    if flagged:
        return f"Flagged {len(flagged)} overdue tasks: {', '.join(flagged)}"
    return "No overdue tasks found."


@tool
def generate_followup_reminders() -> str:
    """
    Check for stale tasks (not updated in 24+ hours) and generate follow-up reminders.
    Increments follow_up_count for each task and logs the reminder.

    Returns:
        List of tasks that need follow-up
    """
    if not _memory_store:
        return "Memory store not initialized"
    stale = _memory_store.get_stale_tasks(hours=24)
    reminders = []
    for task in stale[:5]:
        _memory_store.update_task(
            task.id,
            follow_up_count=task.follow_up_count + 1,
            last_follow_up=datetime.datetime.now().isoformat()
        )
        _memory_store.log_activity("follow_up", "agent", f"Follow-up #{task.follow_up_count+1}: {task.title}", task.id)
        emit(f"📨 Follow-up generated: {task.title} → {task.owner}", "info")
        reminders.append(f"'{task.title}' (owner: {task.owner or 'unassigned'}, follow-up #{task.follow_up_count+1})")
    if reminders:
        return "Follow-ups needed:\n" + "\n".join(reminders)
    return "No stale tasks requiring follow-up."


@tool
def log_agent_activity(action: str, description: str) -> str:
    """
    Log an agent activity to the activity feed visible in the UI.

    Args:
        action: Short action name (e.g. 'sync_complete', 'risk_detected')
        description: Human-readable description of what happened

    Returns:
        Confirmation
    """
    if not _memory_store:
        return "Memory store not initialized"
    _memory_store.log_activity(action, "agent", description)
    emit(f" {description}", "info")
    return f"Logged: {description}"


@tool
def fetch_gmail_messages(query: str = "is:unread", max_results: int = 10) -> str:
    """
    Fetch messages from Gmail and extract tasks from them.
    Uses either real Gmail API or mock responses based on integration mode.

    Args:
        query: Gmail search query (default: "is:unread")
        max_results: Maximum number of messages to fetch (default: 10)

    Returns:
        Summary of messages fetched and tasks extracted
    """
    try:
        from integrations.factory import IntegrationFactory
        
        gmail = IntegrationFactory.create_gmail_integration(_integration_mode)
        gmail.connect()
        
        messages = gmail.fetch_messages(query, max_results)
        tasks = gmail.extract_tasks_from_emails(messages)
        
        # Save extracted tasks
        saved_count = 0
        for task_data in tasks:
            task = Task(
                title=task_data["title"],
                description=task_data["description"],
                source="gmail",
                owner=task_data["owner"],
                priority=task_data["priority"]
            )
            _memory_store.add_task(task)
            saved_count += 1
        
        emit(f" Fetched {len(messages)} Gmail messages, extracted {saved_count} tasks", "success")
        return f"Fetched {len(messages)} Gmail messages and extracted {saved_count} tasks"
        
    except Exception as e:
        emit(f" Gmail fetch error: {e}", "error")
        return f"Error fetching Gmail messages: {str(e)}"


@tool
def fetch_jira_issues(jql: str = "", max_results: int = 50) -> str:
    """
    Fetch issues from Jira and extract tasks from them.
    Uses either real Jira API or mock responses based on integration mode.

    Args:
        jql: JIRA Query Language (default: "" for all issues)
        max_results: Maximum number of issues to fetch (default: 50)

    Returns:
        Summary of issues fetched and tasks extracted
    """
    try:
        from integrations.factory import IntegrationFactory
        
        jira = IntegrationFactory.create_jira_integration(_integration_mode)
        jira.connect()
        
        issues = jira.fetch_issues(jql, max_results)
        tasks = jira.extract_tasks_from_issues(issues)
        
        # Save extracted tasks
        saved_count = 0
        for task_data in tasks:
            task = Task(
                title=task_data["title"],
                description=task_data["description"],
                source="jira",
                owner=task_data["owner"],
                priority=task_data["priority"],
                status=task_data.get("status", "pending"),
                deadline=task_data.get("deadline")
            )
            _memory_store.add_task(task)
            saved_count += 1
        
        emit(f" Fetched {len(issues)} Jira issues, extracted {saved_count} tasks", "success")
        return f"Fetched {len(issues)} Jira issues and extracted {saved_count} tasks"
        
    except Exception as e:
        emit(f" Jira fetch error: {e}", "error")
        return f"Error fetching Jira issues: {str(e)}"


@tool
def fetch_slack_messages(channel_id: str = "C123", limit: int = 20) -> str:
    """
    Fetch messages from Slack and extract tasks from them.
    Uses either real Slack API or mock responses based on integration mode.

    Args:
        channel_id: Slack channel ID (default: "C123")
        limit: Maximum number of messages to fetch (default: 20)

    Returns:
        Summary of messages fetched and tasks extracted
    """
    try:
        from integrations.factory import IntegrationFactory
        
        slack = IntegrationFactory.create_slack_integration(_integration_mode)
        slack.connect()
        
        messages = slack.fetch_messages(channel_id, limit)
        tasks = slack.extract_tasks_from_messages(messages)
        
        # Save extracted tasks
        saved_count = 0
        for task_data in tasks:
            task = Task(
                title=task_data["title"],
                description=task_data["description"],
                source="slack",
                owner=task_data["owner"],
                priority=task_data["priority"]
            )
            _memory_store.add_task(task)
            saved_count += 1
        
        emit(f" Fetched {len(messages)} Slack messages, extracted {saved_count} tasks", "success")
        return f"Fetched {len(messages)} Slack messages and extracted {saved_count} tasks"
        
    except Exception as e:
        emit(f" Slack fetch error: {e}", "error")
        return f"Error fetching Slack messages: {str(e)}"


@tool
def fetch_notion_tasks(database_id: str = "db123") -> str:
    """
    Fetch tasks from Notion database and extract them.
    Uses either real Notion API or mock responses based on integration mode.

    Args:
        database_id: Notion database ID (default: "db123")

    Returns:
        Summary of tasks fetched and extracted
    """
    try:
        from integrations.factory import IntegrationFactory
        
        notion = IntegrationFactory.create_notion_integration(_integration_mode)
        notion.connect()
        
        pages = notion.fetch_database_items(database_id)
        tasks = notion.extract_tasks_from_pages(pages)
        
        # Save extracted tasks
        saved_count = 0
        for task_data in tasks:
            task = Task(
                title=task_data["title"],
                description=task_data["description"],
                source="notion",
                owner=task_data["owner"],
                priority=task_data["priority"],
                status=task_data.get("status", "pending"),
                deadline=task_data.get("deadline")
            )
            _memory_store.add_task(task)
            saved_count += 1
        
        emit(f" Fetched {len(pages)} Notion pages, extracted {saved_count} tasks", "success")
        return f"Fetched {len(pages)} Notion pages and extracted {saved_count} tasks"
        
    except Exception as e:
        emit(f" Notion fetch error: {e}", "error")
        return f"Error fetching Notion tasks: {str(e)}"


@tool
def load_mock_data() -> str:
    """
    Load mock data from all integrations for testing purposes.
    This automatically fetches sample data from Gmail, Jira, Slack, and Notion.

    Returns:
        Summary of all mock data loaded
    """
    if _integration_mode != "mock":
        return "Mock data loading is only available in mock mode"
    
    results = []
    
    try:
        # Load Gmail data - call underlying function directly
        gmail_result = fetch_gmail_messages.func(query="is:unread", max_results=5)
        results.append(f"Gmail: {gmail_result}")
    except Exception as e:
        results.append(f"Gmail error: {e}")
    
    try:
        # Load Jira data - call underlying function directly
        jira_result = fetch_jira_issues.func(jql="", max_results=5)
        results.append(f"Jira: {jira_result}")
    except Exception as e:
        results.append(f"Jira error: {e}")
    
    try:
        # Load Slack data - call underlying function directly
        slack_result = fetch_slack_messages.func(channel_id="C123", limit=5)
        results.append(f"Slack: {slack_result}")
    except Exception as e:
        results.append(f"Slack error: {e}")
    
    try:
        # Load Notion data - call underlying function directly
        notion_result = fetch_notion_tasks.func(database_id="db123")
        results.append(f"Notion: {notion_result}")
    except Exception as e:
        results.append(f"Notion error: {e}")
    
    emit("🎯 Mock data loaded from all integrations", "success")
    return "Mock data loaded:\n" + "\n".join(results)


@tool
def list_available_tools() -> str:
    """
    List all available tools with their descriptions and usage.
    Use this to see what tools are available in the agent.

    Returns:
        Formatted list of all available tools with descriptions
    """
    tools_info = [
        {
            "name": "extract_and_save_tasks",
            "description": "Extract actionable tasks from unstructured text and save them to memory",
            "usage": "Use when user provides text (email, Slack, meeting notes) and wants tasks extracted",
            "example": "extract_and_save_tasks(text='Meeting notes: John will complete the report by Friday', source='manual')"
        },
        {
            "name": "get_task_summary",
            "description": "Get a current summary of all tasks including overdue, pending, and in-progress",
            "usage": "Use to understand current workload before making decisions",
            "example": "get_task_summary()"
        },
        {
            "name": "update_task_status",
            "description": "Update the status or risk level of an existing task",
            "usage": "Use when you need to change task status or mark as overdue",
            "example": "update_task_status(task_id='abc12345', status='completed')"
        },
        {
            "name": "flag_overdue_tasks",
            "description": "Scan all tasks and flag any that are past their deadline",
            "usage": "Use during monitoring cycles to identify overdue items",
            "example": "flag_overdue_tasks()"
        },
        {
            "name": "generate_followup_reminders",
            "description": "Check for stale tasks and generate follow-up reminders",
            "usage": "Use for tasks not updated in 24+ hours",
            "example": "generate_followup_reminders()"
        },
        {
            "name": "log_agent_activity",
            "description": "Log an agent activity to the activity feed visible in the UI",
            "usage": "Use to record important actions or decisions",
            "example": "log_agent_activity(action='task_completed', description='Completed project proposal')"
        },
        {
            "name": "fetch_gmail_messages",
            "description": "Fetch messages from Gmail and extract tasks from them",
            "usage": "Use to get emails and convert them to tasks",
            "example": "fetch_gmail_messages(query='is:unread', max_results=10)"
        },
        {
            "name": "fetch_jira_issues",
            "description": "Fetch issues from Jira and extract tasks from them",
            "usage": "Use to sync Jira issues with task management",
            "example": "fetch_jira_issues(jql='project=PROJ AND status!=Done', max_results=50)"
        },
        {
            "name": "fetch_slack_messages",
            "description": "Fetch messages from Slack and extract tasks from them",
            "usage": "Use to get Slack messages and convert to tasks",
            "example": "fetch_slack_messages(channel_id='C123', limit=20)"
        },
        {
            "name": "fetch_notion_tasks",
            "description": "Fetch tasks from Notion database and extract them",
            "usage": "Use to sync Notion tasks with the agent",
            "example": "fetch_notion_tasks(database_id='db123')"
        },
        {
            "name": "load_mock_data",
            "description": "Load mock data from all integrations for testing purposes",
            "usage": "Use in mock mode to populate sample data",
            "example": "load_mock_data()"
        },
        {
            "name": "list_available_tools",
            "description": "List all available tools with their descriptions and usage",
            "usage": "Use to see what tools are available",
            "example": "list_available_tools()"
        }
    ]
    
    output_lines = ["🔧 **Available Agent Tools:**", ""]
    
    for tool in tools_info:
        output_lines.extend([
            f"📋 **{tool['name']}**",
            f"📝 Description: {tool['description']}",
            f"🎯 Usage: {tool['usage']}",
            f"💡 Example: {tool['example']}",
            f""
        ])
    
    return "\n".join(output_lines)


# All tools in one list for the LLM
AGENT_TOOLS = [
    extract_and_save_tasks,
    get_task_summary,
    update_task_status,
    flag_overdue_tasks,
    generate_followup_reminders,
    log_agent_activity,
    fetch_gmail_messages,
    fetch_jira_issues,
    fetch_slack_messages,
    fetch_notion_tasks,
    load_mock_data,
    list_available_tools,
]
