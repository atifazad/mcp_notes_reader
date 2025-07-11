#!/usr/bin/env python3
"""
Google Calendar Service

Handles Google Calendar operations for the MCP server.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_CALENDAR_SUPPORT = True
except ImportError:
    GOOGLE_CALENDAR_SUPPORT = False

# If modifying these scopes, delete the file token.json.
SCOPES = os.getenv("GOOGLE_SCOPES", "https://www.googleapis.com/auth/calendar").split(",")

class GoogleCalendarService:
    """Service for interacting with Google Calendar."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        if not GOOGLE_CALENDAR_SUPPORT:
            return False
            
        try:
            # The file token.json stores the user's access and refresh tokens,
            # and is created automatically when the authorization flow completes for the first time.
            token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
            credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
            
            if os.path.exists(token_file):
                self.credentials = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    self.credentials.refresh(Request())
                else:
                    # Check if credentials file exists
                    if not os.path.exists(credentials_file):
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES)
                    self.credentials = flow.run_local_server(port=0)
                
                # Save the credentials for the next run with proper permissions
                with open(token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                
                # Set secure file permissions (read/write for owner only)
                os.chmod(token_file, 0o600)
            
            self.service = build('calendar', 'v3', credentials=self.credentials)
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def create_event(self, summary: str, description: str = "", 
                    start_time: Optional[datetime] = None, 
                    end_time: Optional[datetime] = None,
                    location: str = "") -> Dict[str, Any]:
        """
        Create a calendar event.
        
        Args:
            summary: Event title
            description: Event description
            start_time: Start time (defaults to now + 1 hour)
            end_time: End time (defaults to start_time + 1 hour)
            location: Event location
            
        Returns:
            Dictionary with event details or error information
        """
        if not self.service:
            if not self.authenticate():
                return {"error": "Failed to authenticate with Google Calendar"}
        
        try:
            # Set default times if not provided
            if not start_time:
                start_time = datetime.now() + timedelta(hours=1)
            if not end_time:
                end_time = start_time + timedelta(hours=1)
            
            event = {
                'summary': summary,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/Berlin',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Europe/Berlin',
                },
            }
            
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "success": True,
                "event_id": event.get('id'),
                "html_link": event.get('htmlLink'),
                "summary": event.get('summary'),
                "start": event.get('start', {}).get('dateTime'),
                "end": event.get('end', {}).get('dateTime')
            }
            
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}
        except Exception as e:
            return {"error": f"Failed to create event: {e}"}
    
    def list_events(self, max_results: int = 10) -> Dict[str, Any]:
        """
        List upcoming calendar events.
        
        Args:
            max_results: Maximum number of events to return
            
        Returns:
            Dictionary with list of events or error information
        """
        if not self.service:
            if not self.authenticate():
                return {"error": "Failed to authenticate with Google Calendar"}
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=now,
                maxResults=max_results, 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            return {
                "success": True,
                "events": [
                    {
                        "id": event.get('id'),
                        "summary": event.get('summary'),
                        "start": event.get('start', {}),
                        "end": event.get('end', {}),
                        "description": event.get('description', ''),
                        "location": event.get('location', '')
                    }
                    for event in events
                ]
            }
            
        except HttpError as error:
            return {"error": f"An error occurred: {error}"}
        except Exception as e:
            return {"error": f"Failed to list events: {e}"}

def get_calendar_service() -> Optional[GoogleCalendarService]:
    """Get a configured Google Calendar service instance."""
    if not GOOGLE_CALENDAR_SUPPORT:
        return None
    
    service = GoogleCalendarService()
    if service.authenticate():
        return service
    return None 