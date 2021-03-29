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
from datetime import datetime, timedelta
from getpass import getpass
from pathlib import Path
from typing import List, Optional

from furl import furl
from jira import JIRA, Issue

from jotfiles.model import Task
from jotfiles.scrum import ScrumBoard, Sprint

logger = logging.getLogger(__name__)
default_path = Path("credentials_jira.json")
date_format = "%d/%b/%y %I:%M %p"


@dataclass
class Config:
    owner: str
    password: str
    board: int
    server_url: furl


def load_from_file(file: Path = default_path) -> Config:
    with file.open() as f:
        credentials = json.load(f)
        return Config(
            credentials["owner"],
            credentials["pass"],
            credentials["board"],
            furl(credentials["server"]),
        )


def load_from_cli() -> Config:
    return Config(
        input("JIRA Username"),
        getpass("JIRA Password"),
        int(input("Board number")),
        furl(input("Server URL")),
    )


class JiraScrumBoard(ScrumBoard):
    def __init__(self, config: Config):
        self.server_url = config.server_url
        self.owner = config.owner
        self.server = JIRA(str(self.server_url), auth=(self.owner, config.password))
        self.board = config.board

    def create_task(self, issue: Issue, due_date: datetime):
        return Task(
            issue.key,
            issue.fields.summary,
            timedelta(seconds=issue.fields.aggregatetimeestimate),
            due_date,
            self.server_url / "browse" / issue.key,
        )

    def current_sprint(self) -> Sprint:
        sprints = self.server.sprints(self.board)
        logger.debug("Searching for an active sprint in %s sprints", len(sprints))
        summary = next(sprint for sprint in sprints if sprint.state == "ACTIVE")
        jira_sprint = self.server.sprint_info(self.board, summary.id)
        end_date = datetime.strptime(jira_sprint["endDate"], date_format)
        return Sprint(jira_sprint["id"], end_date)

    def current_sprint_tasks(self, assignee: Optional[str] = None) -> List[Task]:
        assignee = assignee or self.owner
        sprint = self.current_sprint()
        due_date = sprint.end_date
        jql = "status !=  Closed AND Sprint = {} AND assignee in ({})".format(
            sprint.id, assignee
        )
        return [
            self.create_task(issue, due_date)
            for issue in self.server.search_issues(jql)
        ]
