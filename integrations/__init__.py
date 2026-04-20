"""
External integrations for Desktop Agent OS
"""

from .slack import SlackIntegration
from .gmail import GmailIntegration
from .notion import NotionIntegration
from .jira import JiraIntegration

__all__ = ['SlackIntegration', 'GmailIntegration', 'NotionIntegration', 'JiraIntegration']
