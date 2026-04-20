"""
Gmail Integration with real API implementation
"""

import os
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailIntegration:
    """
    Gmail Integration with real API implementation.
    
    SETUP:
    1. Enable Gmail API → https://console.developers.google.com
    2. Create OAuth 2.0 Desktop credentials → download credentials.json
    3. Scopes: gmail.readonly, gmail.send, gmail.modify
    4. Set environment variable: GMAIL_CREDENTIALS_PATH
    """
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
              'https://www.googleapis.com/auth/gmail.send',
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.credentials_path = self.config.get('credentials_path') or os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
        self.token_path = self.config.get('token_path') or 'token.json'
        self.service = None
        self.connected = False

    def connect(self, credentials_path: str = None) -> bool:
        """Connect to Gmail API using OAuth2"""
        try:
            creds = None
            token_path = credentials_path or self.token_path
            
            if os.path.exists(token_path):
                creds = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('gmail', 'v1', credentials=creds)
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Error connecting to Gmail: {e}")
            return False

    def fetch_messages(self, query: str = "is:unread", max_results: int = 10) -> List[Dict]:
        """
        Fetch messages from Gmail
        
        GET https://gmail.googleapis.com/gmail/v1/users/me/messages
        Params: q=query, maxResults=max_results
        Then fetch each: GET .../messages/{id}?format=full
        Returns: [{"id": "...", "from": "...", "subject": "...", "body": "...", "date": "..."}]
        """
        if not self.connected or not self.service:
            return []
            
        try:
            messages = []
            result = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            message_ids = result.get('messages', [])
            
            for msg_id in message_ids:
                msg = self.service.users().messages().get(
                    userId='me', id=msg_id['id'], format='full'
                ).execute()
                
                parsed_msg = self._parse_message(msg)
                messages.append(parsed_msg)
                
            return messages
            
        except HttpError as e:
            print(f"Error fetching messages: {e}")
            return []

    def send_message(self, to: str, subject: str, body: str) -> bool:
        """
        Send an email via Gmail
        
        POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
        Create MIME → base64url encode → send as {"raw": encoded}
        Returns: True if sent
        """
        if not self.connected or not self.service:
            return False
            
        try:
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = self.service.users().messages().send(
                userId='me', body={'raw': raw_message}
            ).execute()
            
            print(f"Email sent to {to}, Message ID: {result['id']}")
            return True
            
        except HttpError as e:
            print(f"Error sending email: {e}")
            return False

    def _parse_message(self, message: Dict) -> Dict:
        """Parse Gmail message format"""
        headers = message.get('payload', {}).get('headers', [])
        
        subject = ""
        from_addr = ""
        date = ""
        
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
            elif header['name'].lower() == 'from':
                from_addr = header['value']
            elif header['name'].lower() == 'date':
                date = header['value']
        
        # Extract body
        body = self._extract_body(message.get('payload', {}))
        
        return {
            "id": message['id'],
            "from": from_addr,
            "subject": subject,
            "body": body,
            "date": date
        }
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract body from message payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        return ""
    
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
