"""
Task and activity data models
"""

import datetime
import uuid
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Task:
    """Represents a work task extracted from various sources"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    description: str = ""
    owner: str = ""
    deadline: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    source: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    risk_level: str = "low"
    follow_up_count: int = 0
    last_follow_up: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        try:
            return datetime.datetime.now() > datetime.datetime.fromisoformat(self.deadline) and self.status != "completed"
        except:
            return False

    def days_until_deadline(self) -> Optional[int]:
        if not self.deadline:
            return None
        try:
            return (datetime.datetime.fromisoformat(self.deadline) - datetime.datetime.now()).days
        except:
            return None


@dataclass
class ActivityLog:
    """Represents an activity log entry"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    action: str = ""
    source: str = ""
    description: str = ""
    task_id: Optional[str] = None


@dataclass
class Integration:
    """Represents an external integration configuration"""
    name: str = ""
    status: str = "disconnected"
    last_sync: Optional[str] = None
    config: dict = field(default_factory=dict)
