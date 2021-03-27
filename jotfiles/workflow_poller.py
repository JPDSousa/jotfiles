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

import time
from dataclasses import dataclass
from pathlib import Path

import schedule
from workflow_hooks import LocalWorkflow

from jotfiles.components import PersonalSpace
from jotfiles.jira_m.jira_hooks import JiraScrumBoard
from jotfiles.jira_m.jira_hooks import load_from_file as load_jira_from_file
from jotfiles.scrum import ScrumBoard
from jotfiles.trello_m.trello_hooks import TrelloPersonalSpace
from jotfiles.trello_m.trello_hooks import load_from_file as load_trello_from_file


@dataclass
class Config:
    # TODO use enums
    personal_board: str
    scrum_board: str
    workflow_mode: str
    base_path: Path


def load_personal_space(config: Config) -> PersonalSpace:
    if config.personal_board == "trello":
        config_path = config.base_path / "credentials_trello.json"
        trello_config = load_trello_from_file(config_path)
        return TrelloPersonalSpace(trello_config)
    else:
        raise ValueError(f"Unknown personal space type {config.personal_board}")


def load_scrum_board(config: Config) -> ScrumBoard:
    if config.scrum_board == "jira":
        config_path = config.base_path / "credentials_jira.json"
        jira_config = load_jira_from_file(config_path)
        return JiraScrumBoard(jira_config)
    else:
        raise ValueError(f"Unknown scrum board type {config.scrum_board}")


def bootstrap_poller(config: Config):

    scrum_board = load_scrum_board(config)
    personal_board = load_personal_space(config)

    workflow = LocalWorkflow(scrum_board, personal_board)

    schedule.every().hour.do(workflow.update_sprint_issues)
    schedule.every().hour.do(personal_board.update_done)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    config = Config("trello", "jira", "local", Path().absolute().parent)
    bootstrap_poller(config)
