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

from dependency_injector import containers, providers

from jotfiles.components import PersonalBoard
from jotfiles.comunication import Chat, ScheduledMessagesPool
from jotfiles.google import GChat
from jotfiles.jira_m import Config as JIRAConfig
from jotfiles.jira_m import JiraScrumBoard
from jotfiles.jira_m import load_from_file as load_jira_from_file
from jotfiles.scrum import ScrumBoard
from jotfiles.trello_m import TrelloPersonalBoard, TrelloScheduledMessagesPool
from jotfiles.trello_m import load_from_file as load_trello_from_file
from jotfiles.workflow_hooks import LocalWorkflow


def load_personal_space(config, trello_client, trello_config) -> PersonalBoard:
    personal_board = config["personal_board"]
    if personal_board == "trello":
        return TrelloPersonalBoard(trello_client(), trello_config.board_id)
    else:
        raise ValueError(f"Unknown personal space type {personal_board}")


def load_scrum_board(config, jira_config) -> ScrumBoard:

    scrum_board = config["scrum_board"]
    if scrum_board == "jira":
        return JiraScrumBoard(jira_config)
    else:
        raise ValueError(f"Unknown scrum board type {scrum_board}")


def load_smpool(config, trello_client) -> ScheduledMessagesPool:

    smpool = config["smpool"]
    if smpool == "trello":
        return TrelloScheduledMessagesPool(trello_client())
    else:
        raise ValueError(f"Unknown scheduled messages pool type {smpool}")


def load_chat(config) -> Chat:

    chat = config["chat"]
    if chat == "gchat":
        return GChat({})
    else:
        raise ValueError(f"Unknown chat type {chat}")


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    trello_config = providers.Singleton(
        load_trello_from_file, config.trello_credentials
    )

    trello_client = providers.Singleton(trello_config.provided.create_client)

    personal_board = providers.Singleton(
        load_personal_space, config, trello_client, trello_config
    )

    jira_config: JIRAConfig = providers.Singleton(
        load_jira_from_file, config.jira_credentials
    )

    scrum_board = providers.Singleton(load_scrum_board, config, jira_config)

    smpool = providers.Singleton(load_smpool, config, trello_client)

    chat = providers.Singleton(load_chat, config)

    workflow = providers.Singleton(
        LocalWorkflow, scrum_board, personal_board, smpool, chat
    )
