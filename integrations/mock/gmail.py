"""
Mock Gmail Integration for testing without real API
"""

import random
import datetime
from typing import List, Dict, Optional


class MockGmailIntegration:
    """
    Mock Gmail Integration for testing and development.
    Provides realistic sample data without requiring API credentials.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.connected = False
        
        # Mock data
        self.mock_emails = [
            {
                "id": "msg001",
                "from": "manager@company.com",
                "subject": "Q4 Planning Meeting - Action Items",
                "body": "Hi team, Please prepare your Q4 roadmap presentations. Deadline: Friday EOD. Also, review the attached budget spreadsheet.",
                "date": "2024-01-15T10:30:00Z"
            },
            {
                "id": "msg002",
                "from": "client@external.com",
                "subject": "Urgent: Production Bug Report",
                "body": "We're experiencing critical issues with the payment gateway. Users cannot complete transactions. This needs immediate attention.",
                "date": "2024-01-15T09:15:00Z"
            },
            {
                "id": "msg003",
                "from": "dev-team@company.com",
                "subject": "Code Review Request",
                "body": "Please review pull request #1234 for the new authentication feature. We need to merge this by tomorrow.",
                "date": "2024-01-15T08:45:00Z"
            },
            {
                "id": "msg004",
                "from": "hr@company.com",
                "subject": "Performance Reviews Due",
                "body": "Reminder: Self-assessments are due next Monday. Please complete your performance review forms.",
                "date": "2024-01-14T16:20:00Z"
            },
            {
                "id": "msg005",
                "from": "vendor@partner.com",
                "subject": "Contract Renewal",
                "body": "Our current contract expires in 30 days. Please review the terms and let us know if you'd like to renew.",
                "date": "2024-01-14T14:10:00Z"
            }
        ]

    def connect(self, credentials_path: str = None) -> bool:
        """Mock connection to Gmail"""
        print("[MOCK] Connected to Gmail successfully")
        self.connected = True
        return True

    def fetch_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict]:
        """Mock fetch messages from Gmail"""
        if not self.connected:
            return []
            
        print(f"[MOCK] Fetching messages with query: {query}")
        return random.sample(self.mock_emails, min(max_results, len(self.mock_emails)))

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """Mock send an email via Gmail"""
        if not self.connected:
            return False
            
        print(f"[MOCK] Email sent to {to}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:100]}...")
        return True

    def extract_tasks_from_emails(self, emails: List[Dict]) -> List[Dict]:
        """Extract potential tasks from emails"""
        tasks = []
        for email in emails:
            subject = email.get("subject", "")
            body = email.get("body", "")
            combined_text = f"{subject} {body}"
            
            # Simple task extraction logic
            if any(keyword in combined_text.lower() for keyword in ["deadline", "due", "please", "need to", "review", "complete"]):
                tasks.append({
                    "title": subject[:50] + "..." if len(subject) > 50 else subject,
                    "description": body[:200] + "..." if len(body) > 200 else body,
                    "source": "gmail",
                    "owner": email.get("from", ""),
                    "priority": "high" if "urgent" in combined_text.lower() else "medium"
                })
        return tasks
