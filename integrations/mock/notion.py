"""
Mock Notion Integration for testing without real API
"""

import random
import datetime
from typing import List, Dict, Optional


class MockNotionIntegration:
    """
    Mock Notion Integration for testing and development.
    Provides realistic sample data without requiring API credentials.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.connected = False
        
        # Mock data
        self.mock_databases = [
            {
                "id": "db123",
                "name": "Tasks",
                "items": [
                    {
                        "id": "page001",
                        "properties": {
                            "Name": {"title": [{"text": {"content": "Design new landing page"}}]},
                            "Status": {"select": {"name": "In Progress"}},
                            "Priority": {"select": {"name": "High"}},
                            "Owner": {"people": [{"name": "John Doe"}]},
                            "Due Date": {"date": {"start": "2024-01-20"}}
                        }
                    },
                    {
                        "id": "page002",
                        "properties": {
                            "Name": {"title": [{"text": {"content": "Fix authentication bug"}}]},
                            "Status": {"select": {"name": "To Do"}},
                            "Priority": {"select": {"name": "Critical"}},
                            "Owner": {"people": [{"name": "Jane Smith"}]},
                            "Due Date": {"date": {"start": "2024-01-18"}}
                        }
                    }
                ]
            },
            {
                "id": "db456",
                "name": "Projects",
                "items": [
                    {
                        "id": "page003",
                        "properties": {
                            "Name": {"title": [{"text": {"content": "Q1 Product Launch"}}]},
                            "Status": {"select": {"name": "Planning"}},
                            "Priority": {"select": {"name": "High"}},
                            "Owner": {"people": [{"name": "Mike Johnson"}]}
                        }
                    }
                ]
            }
        ]

    def connect(self, token: str = None) -> bool:
        """Mock connection to Notion"""
        print("[MOCK] Connected to Notion successfully")
        self.connected = True
        return True

    def fetch_database_items(self, database_id: str) -> List[Dict]:
        """Mock fetch items from a Notion database"""
        if not self.connected:
            return []
            
        print(f"[MOCK] Fetching items from database {database_id}")
        for db in self.mock_databases:
            if db["id"] == database_id:
                return db["items"]
        return []

    def create_page(self, database_id: str, properties: Dict) -> Optional[str]:
        """Mock create a new page in Notion"""
        if not self.connected:
            return None
            
        page_id = f"page{random.randint(1000, 9999)}"
        print(f"[MOCK] Created Notion page {page_id} in database {database_id}")
        return page_id

    def get_databases(self) -> List[Dict]:
        """Mock get list of accessible databases"""
        if not self.connected:
            return []
        print("[MOCK] Fetched database list")
        return [{"id": db["id"], "name": db["name"]} for db in self.mock_databases]

    def extract_tasks_from_pages(self, pages: List[Dict]) -> List[Dict]:
        """Extract tasks from Notion pages"""
        tasks = []
        for page in pages:
            props = page.get("properties", {})
            
            # Extract title
            title = ""
            if "Name" in props and "title" in props["Name"]:
                title = props["Name"]["title"][0]["text"]["content"]
            
            # Extract status
            status = "pending"
            if "Status" in props and "select" in props["Status"]:
                status = props["Status"]["select"]["name"].lower().replace(" ", "_")
            
            # Extract priority
            priority = "medium"
            if "Priority" in props and "select" in props["Priority"]:
                priority = props["Priority"]["select"]["name"].lower()
            
            # Extract owner
            owner = ""
            if "Owner" in props and "people" in props["Owner"]:
                owner = props["Owner"]["people"][0]["name"]
            
            # Extract due date
            deadline = ""
            if "Due Date" in props and "date" in props["Due Date"]:
                deadline = props["Due Date"]["date"]["start"]
            
            tasks.append({
                "title": title,
                "description": f"Task from Notion database",
                "source": "notion",
                "owner": owner,
                "priority": priority,
                "status": status,
                "deadline": deadline
            })
        return tasks
