# Internal libs
from dynamics.state import State

from dynamics.task.interface.interface import Interface

from gpt.client import Client
from gpt.message import Message
from gpt.role import Role

from infra.log.loggable import Loggable

# General utilities
from os.path import join, pardir, dirname, realpath
from os import linesep
from typing import List


class Thought(Loggable):
    """
    Builds prompt and asks GPT to think about the current state
    """

    __client: Client = None

    __prompt_front: str = None
    __prompt_mid: str = None
    __prompt_functions: str = None
    __prompt_tail: str = None

    def __init__(self, functions: List[Interface]):

        super().__init__()

        directory: str = realpath(join(dirname(realpath(__file__)), pardir, pardir, "files", "system_prompts"))
        with open(join(directory, "think_front.txt"), "r") as fh:
            self.__prompt_front = fh.read()

        with open(join(directory, "think_mid.txt"), "r") as fh:
            self.__prompt_mid = fh.read()

        self.__prompt_functions = linesep.join([fun.summary for fun in functions])

        with open(join(directory, "think_tail.txt"), "r") as fh:
            self.__prompt_tail = fh.read()

        self.__client = Client()

    def think(self, state: State) -> None:
        """
        Chooses type of the next task based on a given state
        :param state: A State instance
        :return: The chosen LLMInterface instance
        """

        content: str = linesep.join([
            self.__prompt_front,
            state.env_info_string(),
            self.__prompt_mid,
            self.__prompt_functions,
            self.__prompt_tail
        ])

        system_msg: Message = Message(role=Role.SYSTEM, content=content)
        gpt_output: str = self.__client.query_chat(system_msg + state.conversation, temperature=1.0)

        thought: Message = Message(timestamp_start=state.time, role=Role.ASSISTANT, content=gpt_output)
        self._logger.info(thought)
        state.conversation.append(thought)
