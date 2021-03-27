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

from jotfiles.components import PersonalSpace, Workflow
from jotfiles.scrum import ScrumBoard

logger = logging.getLogger(__name__)


# TODO change name
class LocalWorkflow(Workflow):
    def __init__(self, board: ScrumBoard, p_space: PersonalSpace):
        self.board = board
        self.p_space = p_space

    def update_sprint_issues(self):
        for task in self.board.current_sprint_tasks():
            logger.info("Upserting sprint task {}", task.id)
            self.p_space.upsert_task_card(task)
