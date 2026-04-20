"""
Memory store for managing tasks, activity, and integrations
"""

import threading
import datetime
import json
from typing import Optional, List, Dict

from .task import Task, ActivityLog, Integration


class MemoryStore:
    """
    Persistent in-memory store for tasks, activity, and integrations.
    This is separate from LangGraph's state — it holds domain data
    while LangGraph state holds agent execution context.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.activity_log: List[ActivityLog] = []
        self.integrations: Dict[str, Integration] = {
            "slack": Integration(name="Slack"),
            "gmail": Integration(name="Gmail"),
            "notion": Integration(name="Notion"),
            "jira": Integration(name="Jira"),
        }
        self.agent_running: bool = False
        self._lock = threading.Lock()

    def add_task(self, task: Task) -> str:
        with self._lock:
            self.tasks[task.id] = task
            self.log_activity("task_created", "agent", f"Task created: {task.title}", task.id)
            return task.id

    def update_task(self, task_id: str, **kwargs) -> bool:
        with self._lock:
            if task_id not in self.tasks:
                return False
            task = self.tasks[task_id]
            for k, v in kwargs.items():
                if hasattr(task, k):
                    setattr(task, k, v)
            task.updated_at = datetime.datetime.now().isoformat()
            return True

    def get_all_tasks(self) -> List[Task]:
        return list(self.tasks.values())

    def get_overdue_tasks(self) -> List[Task]:
        return [t for t in self.tasks.values() if t.is_overdue()]

    def get_stale_tasks(self, hours: int = 24) -> List[Task]:
        threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return [
            t for t in self.tasks.values()
            if t.status not in ["completed"] and
            datetime.datetime.fromisoformat(t.updated_at) < threshold
        ]

    def log_activity(self, action: str, source: str, description: str, task_id: Optional[str] = None):
        entry = ActivityLog(action=action, source=source, description=description, task_id=task_id)
        self.activity_log.append(entry)
        if len(self.activity_log) > 100:
            self.activity_log = self.activity_log[-100:]

    def get_recent_activity(self, limit: int = 10) -> List[ActivityLog]:
        return sorted(self.activity_log, key=lambda x: x.timestamp, reverse=True)[:limit]

    def update_integration_status(self, name: str, status: str):
        if name in self.integrations:
            self.integrations[name].status = status
            if status == "connected":
                self.integrations[name].last_sync = datetime.datetime.now().isoformat()

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot for LangGraph nodes to read"""
        tasks = self.get_all_tasks()
        return {
            "total_tasks": len(tasks),
            "overdue_count": len(self.get_overdue_tasks()),
            "stale_count": len(self.get_stale_tasks()),
            "connected_integrations": [k for k, v in self.integrations.items() if v.status == "connected"],
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "owner": t.owner,
                    "status": t.status,
                    "priority": t.priority,
                    "deadline": t.deadline,
                    "risk_level": t.risk_level,
                    "follow_up_count": t.follow_up_count,
                    "source": t.source,
                    "is_overdue": t.is_overdue(),
                    "days_until_deadline": t.days_until_deadline(),
                }
                for t in tasks
            ]
        }
