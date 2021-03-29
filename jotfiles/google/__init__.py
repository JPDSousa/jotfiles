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
from typing import Any, Dict

import requests
from furl import furl

from jotfiles.comunication import Chat, Message

logger = logging.getLogger(__name__)


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
