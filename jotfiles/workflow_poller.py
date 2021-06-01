# .venv/bin/python3
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

import logging
import time
from pathlib import Path

import schedule
from pydantic import BaseSettings

from jotfiles.container import Container

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    personal_board: str = "trello"
    scrum_board: str = "jira"
    chat: str = "gchat"
    smpool: str = "trello"
    workflow_mode: str = "local"
    base_path: Path = Path()
    trello_credentials: Path = base_path / "credentials_trello.json"
    jira_credentials: Path = base_path / "credentials_jira.json"


def bootstrap_poller():

    container = Container()
    container.config.from_pydantic(Config())

    workflow = container.workflow()
    personal_board = container.personal_board()

    logger.info("Scheduling actions")
    # this should be dynamic / decoupled
    schedule.every().hour.do(workflow.update_sprint_issues)
    schedule.every().hour.do(personal_board.update_done)
    logger.info("All actions scheduled")

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    bootstrap_poller()
