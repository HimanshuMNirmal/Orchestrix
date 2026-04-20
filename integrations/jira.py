"""
Jira Integration with real API implementation
"""

import os
import base64
import requests
from typing import List, Dict, Optional


class JiraIntegration:
    """
    Jira Integration with real API implementation.
    
    SETUP:
    1. Generate API token → https://id.atlassian.com/manage-profile/security/api-tokens
    2. Set environment variables: JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN
    3. Auth: Basic base64(email:token)
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.base_url = self.config.get('url') or os.getenv('JIRA_URL')
        self.email = self.config.get('email') or os.getenv('JIRA_EMAIL')
        self.api_token = self.config.get('api_token') or os.getenv('JIRA_API_TOKEN')
        self.connected = False
        
        if self.email and self.api_token:
            auth_string = f"{self.email}:{self.api_token}"
            self.auth_header = base64.b64encode(auth_string.encode()).decode()
            self.headers = {
                'Authorization': f'Basic {self.auth_header}',
                'Content-Type': 'application/json'
            }
        else:
            self.headers = {}

    def connect(self, url: str = None, email: str = None, api_token: str = None) -> bool:
        """Connect to Jira API"""
        try:
            self.base_url = url or self.base_url
            self.email = email or self.email
            self.api_token = api_token or self.api_token
            
            if not all([self.base_url, self.email, self.api_token]):
                raise ValueError("Jira URL, email, and API token are required")
            
            # Update auth header
            auth_string = f"{self.email}:{self.api_token}"
            self.auth_header = base64.b64encode(auth_string.encode()).decode()
            self.headers = {
                'Authorization': f'Basic {self.auth_header}',
                'Content-Type': 'application/json'
            }
            
            # Test connection by getting current user
            response = requests.get(
                f"{self.base_url}/rest/api/3/myself",
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.connected = True
                return True
            else:
                print(f"Jira auth failed: {response.json()}")
                return False
                
        except Exception as e:
            print(f"Error connecting to Jira: {e}")
            return False

    def fetch_issues(self, jql: str = "", max_results: int = 50) -> List[Dict]:
        """
        Fetch issues from Jira
        
        GET https://{domain}/rest/api/3/search
        Params: jql, maxResults, fields
        JQL examples:
          - "assignee = currentUser() AND status != Done"
          - "updated >= -24h"
          - "duedate < now() AND status != Done"
        Returns: [{"key": "PROJ-1", "summary": "...", "status": "...", "assignee": "..."}]
        """
        if not self.connected:
            return []
            
        try:
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'summary,status,assignee,priority,description,created,updated,duedate'
            }
            
            response = requests.get(
                f"{self.base_url}/rest/api/3/search",
                headers=self.headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('issues', [])
            
            print(f"Error fetching issues: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching issues: {e}")
            return []

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """
        Add a comment to a Jira issue
        
        POST https://{domain}/rest/api/3/issue/{key}/comment
        Body: Atlassian Document Format (ADF)
        Returns: True if added
        """
        if not self.connected:
            return False
            
        try:
            payload = {
                'body': {
                    'type': 'doc',
                    'version': 1,
                    'content': [
                        {
                            'type': 'paragraph',
                            'content': [
                                {
                                    'type': 'text',
                                    'text': comment
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/comment",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                print(f"Added comment to {issue_key}: {comment[:50]}...")
                return True
            
            print(f"Error adding comment: {response.json()}")
            return False
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False

    def update_issue_status(self, issue_key: str, status: str) -> bool:
        """Update issue status"""
        if not self.connected:
            return False
            
        try:
            payload = {
                'transition': {
                    'id': self._get_transition_id(issue_key, status)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 204:
                print(f"Updated {issue_key} status to {status}")
                return True
            
            print(f"Error updating status: {response.json()}")
            return False
            
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    
    def _get_transition_id(self, issue_key: str, target_status: str) -> str:
        """Get transition ID for status change"""
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                for transition in data.get('transitions', []):
                    if transition['to']['name'].lower() == target_status.lower():
                        return transition['id']
            
            return "31"  # Default transition
            
        except:
            return "31"  # Default transition

    def get_projects(self) -> List[Dict]:
        """Get list of projects"""
        if not self.connected:
            return []
            
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/project",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                projects = []
                for project in data:
                    projects.append({
                        'key': project['key'],
                        'name': project['name']
                    })
                return projects
            
            print(f"Error fetching projects: {response.json()}")
            return []
            
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []

    def extract_tasks_from_issues(self, issues: List[Dict]) -> List[Dict]:
        """Extract tasks from Jira issues"""
        tasks = []
        for issue in issues:
            # Map priority
            priority_map = {
                "Highest": "critical",
                "High": "high",
                "Medium": "medium",
                "Low": "low"
            }
            
            # Map status
            status_map = {
                "To Do": "pending",
                "Open": "pending",
                "In Progress": "in_progress",
                "In Review": "in_progress",
                "Done": "completed",
                "Closed": "completed"
            }
            
            tasks.append({
                "title": issue["summary"],
                "description": issue.get("description", ""),
                "source": "jira",
                "owner": issue.get("assignee", ""),
                "priority": priority_map.get(issue.get("priority", "Medium"), "medium"),
                "status": status_map.get(issue.get("status", "To Do"), "pending"),
                "deadline": issue.get("duedate", ""),
                "external_id": issue["key"]
            })
        return tasks
