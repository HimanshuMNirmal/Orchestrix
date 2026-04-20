"""
Slack Integration with real API implementation
"""

import os
import requests
from typing import List, Dict, Optional


class SlackIntegration:
    """
    Slack Integration with real API implementation.
    
    SETUP:
    1. Create Slack App → https://api.slack.com/apps
    2. Add scopes: channels:history, channels:read, chat:write, users:read
    3. Install to workspace → get Bot Token (xoxb-...)
    4. Set environment variable: SLACK_BOT_TOKEN
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.bot_token = self.config.get('bot_token') or os.getenv('SLACK_BOT_TOKEN')
        self.base_url = "https://slack.com/api"
        self.headers = {
            'Authorization': f'Bearer {self.bot_token}',
            'Content-Type': 'application/json'
        }
        self.connected = False

    def connect(self, bot_token: str = None) -> bool:
        """Connect to Slack API"""
        try:
            token = bot_token or self.bot_token
            if not token:
                raise ValueError("Slack bot token is required")
            
            # Test connection by getting auth info
            response = requests.get(
                f"{self.base_url}/auth.test",
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if response.status_code == 200 and response.json().get('ok'):
                self.connected = True
                if bot_token:
                    self.bot_token = bot_token
                    self.headers['Authorization'] = f'Bearer {bot_token}'
                return True
            else:
                print(f"Slack auth failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error connecting to Slack: {e}")
            return False

    def fetch_messages(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """
        Fetch messages from a Slack channel
        
        GET https://slack.com/api/conversations.history
        Headers: Authorization: Bearer {SLACK_BOT_TOKEN}
        Params: channel, limit, oldest (unix timestamp)
        Returns: [{"user": "U123", "text": "...", "ts": "..."}]
        """
        if not self.connected:
            return []
            
        try:
            params = {
                'channel': channel_id,
                'limit': limit
            }
            
            response = requests.get(
                f"{self.base_url}/conversations.history",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('messages', [])
            
            print(f"Error fetching messages: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []

    def send_message(self, channel_id: str, text: str) -> bool:
        """
        Send a message to a Slack channel
        
        POST https://slack.com/api/chat.postMessage
        Body: {"channel": channel_id, "text": text}
        Returns: True if ok
        """
        if not self.connected:
            return False
            
        try:
            payload = {
                'channel': channel_id,
                'text': text
            }
            
            response = requests.post(
                f"{self.base_url}/chat.postMessage",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print(f"Message sent to {channel_id}: {text[:50]}...")
                    return True
            
            print(f"Error sending message: {response.json()}")
            return False
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def get_channels(self) -> List[Dict]:
        """Get list of channels"""
        if not self.connected:
            return []
            
        try:
            params = {
                'exclude_archived': True,
                'limit': 100
            }
            
            response = requests.get(
                f"{self.base_url}/conversations.list",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('channels', [])
            
            print(f"Error fetching channels: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching channels: {e}")
            return []

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
