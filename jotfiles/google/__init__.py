#  MIT License
#
#  Copyright (c) 2021 João Sousa
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import json
import logging
import os.path
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List

import requests
from furl import furl
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from jotfiles.components import Calendar
from jotfiles.comunication import Chat, Message
from jotfiles.model import CalendarEvent

logger = logging.getLogger(__name__)


# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar.readonly",
]


class GChat(Chat):
    def __init__(self, recipients: Dict[str, furl]):
        self.recipients = recipients

    def send_message(self, message: Message):
        recipient = message.recipient
        if recipient not in self.recipients:
            raise ValueError(
                f"Unknown recipient {recipient}. Available: "
                f"{self.recipients.keys()}"
            )
        webhook = self.recipients[recipient]
        self._send_message({"text": message.content}, message.thread, webhook)

    def _send_message(self, message: Any, thread_key: str, webhook: furl):
        logger.debug("Sending message: %s", message)
        query = {"threadKey": thread_key}
        r = requests.post(
            str(webhook),
            params=query,
            data=json.dumps(message),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        logger.debug("Message sent: %s", r.text)


class GoogleCalendar(Calendar):
    def __init__(self, email):
        self.email = email

        self.creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                self.creds = flow.run_local_server(port=6497)
            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(self.creds, token)

        self.docs_service = build("docs", "v1", credentials=self.creds)
        self.calendar_service = build("calendar", "v3", credentials=self.creds)

    # TODO add list type
    def list_calendars(self) -> List:
        events_result = self.calendar_service.calendarList().list().execute()
        return events_result.get("items", [])

    def list_week_events(self) -> List[CalendarEvent]:
        # Call the Calendar API
        now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        timeMax = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        print("Getting the upcoming 10 events")
        events_result = (
            self.calendar_service.events()
            .list(
                calendarId=self.email,
                timeMin=now,
                timeMax=timeMax,
                maxAttendees=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        attended_events = []
        for event in events_result.get("items", []):
            for attendee in event["attendees"]:
                if (
                    attendee["email"] == self.email
                    and attendee["responseStatus"] == "accepted"
                ):
                    # TODO fix type
                    attended_events.append(event)
                    break
        return attended_events
        # if not events:
        #     print('No upcoming events found.')
        # for event in events:
        #     start = event['start'].get('dateTime', event['start'].get('date'))
        #     print(start, event['summary'])
