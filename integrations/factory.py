"""
Integration Factory - Switch between real and mock integrations
"""

import os
from typing import Union

# Real integrations
from .gmail import GmailIntegration
from .jira import JiraIntegration
from .slack import SlackIntegration
from .notion import NotionIntegration

# Mock integrations
from .mock.gmail import MockGmailIntegration
from .mock.jira import MockJiraIntegration
from .mock.slack import MockSlackIntegration
from .mock.notion import MockNotionIntegration


class IntegrationFactory:
    """Factory to create either real or mock integrations based on mode"""
    
    @staticmethod
    def create_gmail_integration(mode: str = "mock", config: dict = None) -> Union[GmailIntegration, MockGmailIntegration]:
        """
        Create Gmail integration
        
        Args:
            mode: "real" or "mock"
            config: Configuration dictionary
            
        Returns:
            GmailIntegration or MockGmailIntegration instance
        """
        if mode.lower() == "real":
            return GmailIntegration(config)
        else:
            return MockGmailIntegration(config)
    
    @staticmethod
    def create_jira_integration(mode: str = "mock", config: dict = None) -> Union[JiraIntegration, MockJiraIntegration]:
        """
        Create Jira integration
        
        Args:
            mode: "real" or "mock"
            config: Configuration dictionary
            
        Returns:
            JiraIntegration or MockJiraIntegration instance
        """
        if mode.lower() == "real":
            return JiraIntegration(config)
        else:
            return MockJiraIntegration(config)
    
    @staticmethod
    def create_slack_integration(mode: str = "mock", config: dict = None):
        """Create Slack integration"""
        if mode.lower() == "real":
            return SlackIntegration(config)
        else:
            return MockSlackIntegration(config)
    
    @staticmethod
    def create_notion_integration(mode: str = "mock", config: dict = None):
        """Create Notion integration"""
        if mode.lower() == "real":
            return NotionIntegration(config)
        else:
            return MockNotionIntegration(config)
    
    @staticmethod
    def get_all_integrations(mode: str = "mock", config: dict = None) -> dict:
        """
        Get all available integrations
        
        Args:
            mode: "real" or "mock"
            config: Configuration dictionary
            
        Returns:
            Dictionary with all integration instances
        """
        return {
            'gmail': IntegrationFactory.create_gmail_integration(mode, config),
            'jira': IntegrationFactory.create_jira_integration(mode, config),
            'slack': IntegrationFactory.create_slack_integration(mode, config),
            'notion': IntegrationFactory.create_notion_integration(mode, config)
        }
