"""
Mock integrations for testing without real API connections
"""

from .gmail import MockGmailIntegration
from .slack import MockSlackIntegration
from .notion import MockNotionIntegration
from .jira import MockJiraIntegration

__all__ = ['MockGmailIntegration', 'MockSlackIntegration', 'MockNotionIntegration', 'MockJiraIntegration']
