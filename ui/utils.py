"""
UI utility functions
"""

import datetime


class DateUtils:
    @staticmethod
    def format_relative(iso_string: str) -> str:
        try:
            dt = datetime.datetime.fromisoformat(iso_string)
            delta = datetime.datetime.now() - dt
            if delta.days > 0:
                return f"{delta.days}d ago"
            elif delta.seconds > 3600:
                return f"{delta.seconds // 3600}h ago"
            elif delta.seconds > 60:
                return f"{delta.seconds // 60}m ago"
            return "just now"
        except:
            return iso_string

    @staticmethod
    def format_deadline(iso_string: str) -> str:
        if not iso_string:
            return "—"
        try:
            dt = datetime.datetime.fromisoformat(iso_string)
            delta = dt - datetime.datetime.now()
            if delta.days < 0:
                return f"⚠️ {abs(delta.days)}d overdue"
            elif delta.days == 0:
                return "🔴 Due today"
            elif delta.days == 1:
                return "🟡 Due tomorrow"
            elif delta.days <= 7:
                return f"🟠 {delta.days}d left"
            return dt.strftime("%b %d, %Y")
        except:
            return iso_string
