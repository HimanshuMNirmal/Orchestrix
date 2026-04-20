"""
Notion Integration with real API implementation
"""

import os
import requests
from typing import List, Dict, Optional


class NotionIntegration:
    """
    Notion Integration with real API implementation.
    
    SETUP:
    1. Create integration → https://www.notion.so/my-integrations
    2. Get Internal Integration Token
    3. Share target databases with the integration
    4. Set environment variable: NOTION_TOKEN
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.token = self.config.get('token') or os.getenv('NOTION_TOKEN')
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Notion-Version': '2022-06-28'
        }
        self.connected = False

    def connect(self, token: str = None) -> bool:
        """Connect to Notion API"""
        try:
            token_to_use = token or self.token
            if not token_to_use:
                raise ValueError("Notion token is required")
            
            # Test connection by getting user info
            headers = {
                'Authorization': f'Bearer {token_to_use}',
                'Notion-Version': '2022-06-28'
            }
            
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=headers
            )
            
            if response.status_code == 200:
                self.connected = True
                if token:
                    self.token = token
                    self.headers['Authorization'] = f'Bearer {token}'
                return True
            else:
                print(f"Notion auth failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error connecting to Notion: {e}")
            return False

    def fetch_database_items(self, database_id: str) -> List[Dict]:
        """
        Fetch items from a Notion database
        
        POST https://api.notion.com/v1/databases/{id}/query
        Headers: Authorization: Bearer {NOTION_TOKEN}, Notion-Version: 2022-06-28
        Body: {"filter": {...}, "sorts": [...]}
        Returns: list of page property objects
        """
        if not self.connected:
            return []
            
        try:
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json={}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            
            print(f"Error fetching database items: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching database items: {e}")
            return []

    def create_page(self, database_id: str, properties: Dict) -> Optional[str]:
        """
        Create a new page in Notion
        
        POST https://api.notion.com/v1/pages
        Body: {"parent": {"database_id": id}, "properties": {...}}
        Returns: created page ID
        """
        if not self.connected:
            return None
            
        try:
            payload = {
                'parent': {'database_id': database_id},
                'properties': properties
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                page_id = data.get('id')
                print(f"Created Notion page {page_id} in database {database_id}")
                return page_id
            
            print(f"Error creating page: {response.json()}")
            return None
            
        except Exception as e:
            print(f"Error creating page: {e}")
            return None

    def get_databases(self) -> List[Dict]:
        """Get list of accessible databases"""
        if not self.connected:
            return []
            
        try:
            response = requests.post(
                f"{self.base_url}/search",
                headers=self.headers,
                json={'filter': {'property': 'object', 'value': 'database'}}
            )
            
            if response.status_code == 200:
                data = response.json()
                databases = []
                for db in data.get('results', []):
                    databases.append({
                        'id': db['id'],
                        'name': db['title'][0]['text']['content'] if db.get('title') else 'Untitled'
                    })
                return databases
            
            print(f"Error fetching databases: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching databases: {e}")
            return []

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
