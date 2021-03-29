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
from dataclasses import dataclass
from pathlib import Path
from typing import List

from trello import Card, Label, TrelloClient

from jotfiles.components import PersonalBoard
from jotfiles.comunication import ScheduledMessage, ScheduledMessagesPool
from jotfiles.dates.formats import iso_8601
from jotfiles.model import CalendarEvent, Task

default_path = Path("credentials_trello.json")
logger = logging.getLogger(__name__)


@dataclass
class Config:
    api_key: str
    token: str
    board_id: str

    def create_client(self) -> TrelloClient:
        return TrelloClient(api_key=self.api_key, token=self.token)


def load_from_file(file: Path = default_path) -> Config:
    with file.open() as f:
        credentials = json.load(f)
        return Config(
            credentials["api_key"], credentials["token"], credentials["board_id"]
        )


class TrelloScheduledMessagesPool(ScheduledMessagesPool):
    def __init__(self, client: TrelloClient):
        self.client = client

    def list_messages(self) -> List[ScheduledMessage]:
        query = "comment:send message is:open"
        messages = []
        for card in self.client.search(query, models=["cards"]):
            card: Card = card
            messages.append(*card.comments)
        return messages


class TrelloPersonalBoard(PersonalBoard):
    def __init__(self, client: TrelloClient, board_id: str):
        self.client = client
        self.board = self.client.get_board(board_id)
        # name to id map
        self.trello_lists = {tl.name: tl.id for tl in self.board.all_lists()}
        # cache labels
        self.labels = self.board.get_labels()
        self.custom_fields = {
            cf.name: cf for cf in self.board.get_custom_field_definitions()
        }

    def create_review_card(self, name, desc):
        pass
        # today_team.add_card(name, desc, [support_review])

    def _search_open_cards(self, query: str) -> List[Card]:
        return self.client.search(
            f"{query} is:open", models=["cards"], board_ids=[self.board.id]
        )

    def upsert_task_card(self, task: Task):
        key = task.id
        task_comment = f"task_id_{key}"
        cards2update = self._search_open_cards(f"comment:{task_comment}")
        if len(cards2update) > 1:
            logger.warning(
                "Multiple cards exist for task %s. Consider breaking the "
                "task into multiple ones, or use a trello checklist",
                key,
            )
        elif len(cards2update) == 0:
            logger.debug("Fetching backlog list")
            backlog = self.board.get_list(self.trello_lists["[Backlog] On Hold"])
            logger.debug("Adding card to the list")
            ls = [self._label("task:sprint")]
            due = task.due_date.strftime(iso_8601)
            card = backlog.add_card(task.title, position=0, labels=ls, due=due)
            logger.debug("Setting custom task field")
            card.set_custom_field(key, self.custom_fields["Task"])
            card.comment(task_comment)
            cards2update = [card]
        for card in cards2update:
            logger.debug("Syncing card %s with task %s", card.name, key)
            self._update_card(card, task)

    def upsert_calendar_card(self, event: CalendarEvent):
        event_id = event.id
        cards2update = self._search_open_cards(event_id)
        if len(cards2update) > 1:
            raise ValueError(
                f"Multiple cards associated with the same event {cards2update}"
            )
        elif len(cards2update) == 0:
            pass

    def _update_card(self, card: Card, task: Task):
        self._update_remaining(task, card)
        card.attach("Task URL", url=str(task.url))

    def _update_remaining(self, task: Task, card: Card):
        logger.debug("Setting custom remaining field")
        remaining_sec = str(task.remaining.total_seconds() / 3600)
        card.set_custom_field(remaining_sec, self.custom_fields["Time (h)"])

    def update_done(self):
        logger.info("Fetching done cards")
        done_list = self.board.get_list(self.trello_lists["Done"])
        for card in done_list.list_cards():
            if card.due_date:
                logger.debug("Setting card %s due complete", card.name)
                card.set_due_complete()
        logger.info("Update complete")

    def _label(self, name: str) -> Label:
        return next(label for label in self.labels if label.name == name)

    def _bot_comment(self, message: str) -> str:
        return f"BOT {message}"
