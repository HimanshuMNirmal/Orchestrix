# Orchestrix

**Orchestrix** is a powerful desktop agent OS built with LangGraph that integrates seamlessly with your favorite productivity tools. It connects to Gmail, Slack, Notion, and Jira to provide a unified task management and automation experience.

## 🚀 Features

### 📧 **Email Integration**
- **Gmail Integration**: Read, send, and manage emails with OAuth2 authentication
- **Smart Task Extraction**: Automatically identify tasks from email content
- **Real-time Updates**: Monitor unread messages and important communications

### 💬 **Team Communication**
- **Slack Integration**: Access channels, read messages, and send updates
- **Message Analysis**: Extract actionable items from team discussions
- **Automated Responses**: Smart replies based on context

### 📝 **Knowledge Management**
- **Notion Integration**: Query databases, create pages, and manage tasks
- **Structured Data**: Organize information in custom databases
- **Cross-platform Sync**: Keep data consistent across tools

### 🎯 **Project Management**
- **Jira Integration**: Track issues, update status, and manage projects
- **Workflow Automation**: Move tickets through development pipeline
- **Progress Monitoring**: Real-time project status updates

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Gmail API    │    │   Slack API    │    │  Notion API    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Integration Layer    │
                    │  (Gmail/Slack/      │
                    │   Notion/Jira)      │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   LangGraph Core     │
                    │   (Agent Logic)     │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │      UI Layer        │
                    │   (Desktop App)     │
                    └──────────────────────┘
```

## 📸 Screenshots

### Main Dashboard
![Main Dashboard](assets/dashboard.png)
*Central hub for all integrations and task management*

### Integration Setup
![Integration Setup](assets/setup.png)
*Easy configuration for all connected services*

### Chat Interface
![Chat Interface](assets/chat.png)
*Natural language interface for agent interaction*

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/orchestrix.git
   cd orchestrix
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

5. **Run the application**
   ```bash
   python index.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Gmail Integration
GMAIL_CREDENTIALS_PATH=credentials.json

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Notion Integration
NOTION_TOKEN=secret_your_notion_integration_token

# Jira Integration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
```

### Service Setup

#### Gmail
1. Go to [Google Cloud Console](https://console.developers.google.com)
2. Enable Gmail API
3. Create OAuth 2.0 Desktop App credentials
4. Download `credentials.json` to project root

#### Slack
1. Create app at [Slack API](https://api.slack.com/apps)
2. Add bot token scopes: `channels:history`, `channels:read`, `chat:write`, `users:read`
3. Install app and copy bot token

#### Notion
1. Create integration at [Notion](https://www.notion.so/my-integrations)
2. Copy integration token
3. Share databases with your integration

#### Jira
1. Generate API token at [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Configure JIRA_URL, JIRA_EMAIL, and JIRA_API_TOKEN

## 📚 Usage

### LangGraph Agent Tools

The Orchestrix agent includes 12 powerful tools for task management and automation. These tools are automatically available through the chat interface and can be invoked by natural language commands.

#### 🔧 Task Management Tools

**1. extract_and_save_tasks**
- **Purpose**: Extract actionable tasks from any text (emails, meeting notes, Slack messages)
- **Usage**: "Extract tasks from: 'John will finish the report by Friday, Sarah needs to review the code'"
- **When to use**: When you paste text and want to create tasks from it

**2. get_task_summary**
- **Purpose**: Shows all your current tasks in a human-readable format
- **Usage**: "what are my tasks?" or "show me my tasks"
- **Output**: Formatted list with status, priority, and owner information

**3. update_task_status**
- **Purpose**: Changes task status (pending → in-progress → completed)
- **Usage**: "Mark task abc12345 as completed"
- **Parameters**: task_id, status, optional risk_level

#### 🔍 Monitoring Tools

**4. flag_overdue_tasks**
- **Purpose**: Automatically finds and marks past-due tasks as overdue
- **Usage**: Runs automatically during monitoring cycles
- **Action**: Changes status to "overdue" and risk level to "critical"

**5. generate_followup_reminders**
- **Purpose**: Identifies stale tasks (not updated in 24+ hours) and creates follow-ups
- **Usage**: Runs automatically during monitoring cycles
- **Action**: Increments follow-up count and logs reminders

#### 📝 Logging Tools

**6. log_agent_activity**
- **Purpose**: Records important actions and decisions in the activity feed
- **Usage**: "Logged: Completed project proposal review"
- **Parameters**: action, description

#### 🌐 Integration Tools

**7. fetch_gmail_messages**
- **Purpose**: Gets emails from Gmail and converts them to tasks
- **Usage**: "Get unread emails from Gmail"
- **Parameters**: query, max_results

**8. fetch_jira_issues**
- **Purpose**: Pulls Jira tickets and creates tasks from them
- **Usage**: "Sync Jira issues with my tasks"
- **Parameters**: jql, max_results

**9. fetch_slack_messages**
- **Purpose**: Gets Slack messages and extracts action items
- **Usage**: "Check Slack for new tasks"
- **Parameters**: channel_id, limit

**10. fetch_notion_tasks**
- **Purpose**: Imports tasks from Notion databases
- **Usage**: "Import my Notion tasks"
- **Parameters**: database_id

#### 🧪 Testing & Info Tools

**11. load_mock_data**
- **Purpose**: Loads sample data from all integrations for testing
- **Usage**: "Load mock data" (in mock mode)
- **Action**: Creates sample tasks from Gmail, Jira, Slack, and Notion

**12. list_available_tools**
- **Purpose**: Shows complete list of all tools with descriptions
- **Usage**: "what tools are available?" or "help"
- **Output**: Detailed information about every tool

### 💬 Chat Interface Usage

The Orchestrix agent provides an intelligent chat interface that understands natural language commands. Here's how to interact with different types of requests:

#### Task Management Commands

**View Tasks:**
```
what are my tasks?
show me my tasks
task summary
```

**Create Tasks:**
```
create task: Review the quarterly report by Friday
add task: Call the client about the project
new task: Finish the presentation by Monday
I need to complete the code review by Wednesday
```

**Update Tasks:**
```
mark task abc12345 as completed
update task def67890 status to in-progress
complete task ghi12345
```

#### Information Commands

**Available Tools:**
```
what tools are available?
show me all tools
help
list tools
```

**General Assistance:**
```
How do I extract tasks from an email?
What can you do?
Show me overdue tasks
```

#### Integration Commands

**Fetch Data:**
```
Get unread emails from Gmail
Check Slack for new tasks
Sync Jira issues with my tasks
Import my Notion tasks
```

#### Smart Responses

The chat interface intelligently detects your intent and responds appropriately:
- **Task queries** → Direct task summary
- **Creation requests** → Task extraction guidance
- **Update requests** → Status change instructions
- **Tool inquiries** → Complete tool documentation
- **General conversation** → LLM-powered assistance

#### Example Conversations

**Creating a Task:**
```
You: create task: Review the quarterly report by Friday
Agent: I'll extract that as a task for you.
✅ Task saved: Review the quarterly report by Friday
```

**Viewing Tasks:**
```
You: what are my tasks?
Agent: 📊 **Task Summary (16 total tasks)**
⚠️ Overdue: 2
📋 **Current Tasks:**
1. 🟡 🟠 Urgent: Production Bug Report (Owner: client@external.com)
2. 🟡 🟡 Code Review Request (Owner: dev-team@company.com)
...
```

**Getting Help:**
```
You: help
Agent: 🔧 **Available Agent Tools:**
📋 **extract_and_save_tasks**
📝 Description: Extract actionable tasks from unstructured text...
...
```

### Basic Integration Usage

```python
from integrations import GmailIntegration, SlackIntegration, NotionIntegration, JiraIntegration

# Initialize integrations
gmail = GmailIntegration()
slack = SlackIntegration()
notion = NotionIntegration()
jira = JiraIntegration()

# Connect to services
gmail.connect()
slack.connect()
notion.connect()
jira.connect()

# Fetch data
emails = gmail.fetch_messages("is:unread")
messages = slack.fetch_messages("C123456")
tasks = notion.fetch_database_items("database_id")
issues = jira.fetch_issues("assignee = currentUser()")
```

### Task Extraction

```python
# Extract tasks from different sources
email_tasks = gmail.extract_tasks_from_emails(emails)
slack_tasks = slack.extract_tasks_from_messages(messages)
notion_tasks = notion.extract_tasks_from_pages(tasks)
jira_tasks = jira.extract_tasks_from_issues(issues)

# All tasks follow standard format
for task in email_tasks:
    print(f"Task: {task['title']}")
    print(f"Priority: {task['priority']}")
    print(f"Source: {task['source']}")
```

## 🧪 Development

### Mock Integration for Testing

For development without real API keys, use the mock integrations:

```python
from integrations.mock import MockGmailIntegration, MockSlackIntegration

# Use mock implementations
gmail = MockGmailIntegration()
slack = MockSlackIntegration()

# Works exactly like real integrations but with sample data
emails = gmail.fetch_messages()
messages = slack.fetch_messages()
```

### Project Structure

```
orchestrix/
├── integrations/
│   ├── __init__.py
│   ├── gmail.py
│   ├── slack.py
│   ├── notion.py
│   ├── jira.py
│   └── mock/
│       ├── __init__.py
│       ├── gmail.py
│       ├── slack.py
│       ├── notion.py
│       └── jira.py
├── agent/
├── models/
├── ui/
├── utils/
├── assets/
├── index.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) for the agent framework
- [Google APIs](https://developers.google.com/gmail/api) for Gmail integration
- [Slack API](https://api.slack.com/) for team communication
- [Notion API](https://developers.notion.com/) for knowledge management
- [Jira API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/) for project management

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/orchestrix/issues) page
2. Create a new issue with detailed information
3. Join our [Discord community](https://discord.gg/orchestrix)

---

**Built with ❤️ by the Orchestrix team**
