"""
Mock Jira Integration for testing without real API
"""

import random
import datetime
from typing import List, Dict, Optional


class MockJiraIntegration:
    """
    Mock Jira Integration for testing and development.
    Provides realistic sample data without requiring API credentials.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.connected = False
        
        # Mock data
        self.mock_issues = [
            {
                "key": "PROJ-001",
                "summary": "Implement user authentication system",
                "status": "In Progress",
                "assignee": "john.doe@company.com",
                "priority": "High",
                "description": "Add OAuth 2.0 authentication with Google and GitHub providers",
                "created": "2024-01-10T09:00:00Z",
                "updated": "2024-01-15T14:30:00Z",
                "duedate": "2024-01-25T00:00:00Z"
            },
            {
                "key": "PROJ-002",
                "summary": "Fix payment processing bug",
                "status": "Open",
                "assignee": "jane.smith@company.com",
                "priority": "Highest",
                "description": "Customers report payment failures during checkout process",
                "created": "2024-01-14T11:15:00Z",
                "updated": "2024-01-15T10:20:00Z",
                "duedate": "2024-01-17T00:00:00Z"
            },
            {
                "key": "PROJ-003",
                "summary": "Update API documentation",
                "status": "To Do",
                "assignee": "mike.johnson@company.com",
                "priority": "Medium",
                "description": "Document all REST API endpoints with examples",
                "created": "2024-01-12T13:45:00Z",
                "updated": "2024-01-12T13:45:00Z",
                "duedate": "2024-01-30T00:00:00Z"
            },
            {
                "key": "PROJ-004",
                "summary": "Design new dashboard UI",
                "status": "In Review",
                "assignee": "sarah.wilson@company.com",
                "priority": "Low",
                "description": "Create mockups for new analytics dashboard",
                "created": "2024-01-08T16:20:00Z",
                "updated": "2024-01-14T09:10:00Z",
                "duedate": "2024-02-05T00:00:00Z"
            },
            {
                "key": "PROJ-005",
                "summary": "Optimize database queries",
                "status": "In Progress",
                "assignee": "tom.brown@company.com",
                "priority": "High",
                "description": "Improve performance of slow-running queries in reports module",
                "created": "2024-01-11T10:30:00Z",
                "updated": "2024-01-15T15:45:00Z",
                "duedate": "2024-01-20T00:00:00Z"
            }
        ]

    def connect(self, url: str = None, email: str = None, api_token: str = None) -> bool:
        """Mock connection to Jira"""
        print("[MOCK] Connected to Jira successfully")
        self.connected = True
        return True

    def fetch_issues(self, jql: str = "", max_results: int = 50) -> List[Dict]:
        """Mock fetch issues from Jira"""
        if not self.connected:
            return []
            
        print(f"[MOCK] Fetching issues with JQL: {jql}")
        
        # Filter based on simple JQL simulation
        issues = self.mock_issues.copy()
        
        if "overdue" in jql.lower():
            today = datetime.datetime.now()
            issues = [i for i in issues if datetime.datetime.fromisoformat(i.get("duedate", "").replace("Z", "+00:00")) < today]
        
        if "assignee = currentuser()" in jql.lower():
            issues = [i for i in issues if i.get("assignee") == "current.user@company.com"]
        
        return issues[:max_results]

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Mock add a comment to a Jira issue"""
        if not self.connected:
            return False
            
        print(f"[MOCK] Added comment to {issue_key}: {comment[:50]}...")
        return True

    def update_issue_status(self, issue_key: str, status: str) -> bool:
        """Mock update issue status"""
        if not self.connected:
            return False
            
        for issue in self.mock_issues:
            if issue["key"] == issue_key:
                issue["status"] = status
                issue["updated"] = datetime.datetime.now().isoformat() + "Z"
                print(f"[MOCK] Updated {issue_key} status to {status}")
                return True
        return False

    def get_projects(self) -> List[Dict]:
        """Mock get list of projects"""
        if not self.connected:
            return []
        print("[MOCK] Fetched project list")
        return [
            {"key": "PROJ", "name": "Main Project"},
            {"key": "SUP", "name": "Support"},
            {"key": "DOC", "name": "Documentation"}
        ]

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
