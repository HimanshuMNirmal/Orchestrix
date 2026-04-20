"""
Mock Slack Integration for testing without real API
"""

import random
import datetime
from typing import List, Dict, Optional


class MockSlackIntegration:
    """
    Mock Slack Integration for testing and development.
    Provides realistic sample data without requiring API credentials.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.connected = False
        
        # Mock data
        self.mock_messages = [
            {"user": "U123", "text": "Need to review the Q4 roadmap by Friday", "ts": "1699876543"},
            {"user": "U456", "text": "Can someone update the API documentation?", "ts": "1699876500"},
            {"user": "U789", "text": "Meeting tomorrow at 2 PM to discuss sprint planning", "ts": "1699876400"},
            {"user": "U321", "text": "Bug found in production - urgent fix needed", "ts": "1699876300"},
            {"user": "U654", "text": "Please review my pull request for the new feature", "ts": "1699876200"},
        ]
        
        self.mock_channels = [
            {"id": "C123", "name": "general"},
            {"id": "C456", "name": "development"},
            {"id": "C789", "name": "random"},
        ]

    def connect(self, bot_token: str = None) -> bool:
        """Mock connection to Slack"""
        print("[MOCK] Connected to Slack successfully")
        self.connected = True
        return True

    def fetch_messages(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """Mock fetch messages from a Slack channel"""
        if not self.connected:
            return []
            
        print(f"[MOCK] Fetching {limit} messages from channel {channel_id}")
        return random.sample(self.mock_messages, min(limit, len(self.mock_messages)))

    def send_message(self, channel_id: str, text: str) -> bool:
        """Mock send a message to a Slack channel"""
        if not self.connected:
            return False
            
        print(f"[MOCK] Slack message sent to {channel_id}: {text}")
        return True

    def get_channels(self) -> List[Dict]:
        """Mock get list of channels"""
        if not self.connected:
            return []
        print("[MOCK] Fetched channel list")
        return self.mock_channels

    def extract_tasks_from_messages(self, messages: List[Dict]) -> List[Dict]:
        """Extract potential tasks from Slack messages"""
        tasks = []
        for msg in messages:
            text = msg.get("text", "")
            # Simple task extraction logic
            if any(keyword in text.lower() for keyword in ["need to", "please", "review", "fix", "update"]):
                tasks.append({
                    "title": text[:50] + "..." if len(text) > 50 else text,
                    "description": text,
                    "source": "slack",
                    "owner": f"user_{msg['user']}",
                    "priority": "medium" if "urgent" not in text.lower() else "high"
                })
        return tasks
