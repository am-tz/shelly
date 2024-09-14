# Internal libs
from dynamics.state import State

from dynamics.task.interface.interface import Interface

from gpt.client import Client
from gpt.conversation import Message
from gpt.role import Role

from infra.log.loggable import Loggable

# General utilities
from datetime import datetime
from os.path import join, pardir, dirname, realpath
from os import linesep
from typing import List


class Choice(Loggable):
    """
    Builds prompt and asks GPT to choose the next task type
    """

    __client: Client = None

    __prompt_front: str = None
    __prompt_mid: str = None
    __prompt_functions: str = None
    __prompt_tail: str = None

    __functions: List[Interface] = None

    def __init__(self, functions: List[Interface]):

        super().__init__()

        directory: str = realpath(join(dirname(realpath(__file__)), pardir, pardir, "files", "system_prompts"))
        with open(join(directory, "choose_front.txt"), "r") as fh:
            self.__prompt_front = fh.read()

        with open(join(directory, "choose_mid.txt"), "r") as fh:
            self.__prompt_mid = fh.read()

        self.__functions = functions
        self.__prompt_functions = linesep.join([fun.name for fun in functions])

        with open(join(directory, "choose_tail.txt"), "r") as fh:
            self.__prompt_tail = fh.read()

        self.__client = Client()

    def make(self, state: State) -> Interface | None:
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

        gpt_output: str = self.__client.query_chat(system_msg + state.conversation, temperature=0.1)

        function_names: List[str] = [fun.name for fun in self.__functions]
        result_message_str: str
        result: Interface | None = None
        if gpt_output in function_names:
            result_message_str = f"Chose next task: '{gpt_output}'"
            self._logger.info(result_message_str)

            result = self.__functions[function_names.index(gpt_output)]
        else:
            result_message_str = f"Chose non-existent task '{gpt_output}'"
            self._logger.warning(result_message_str)

        result_message: Message = Message(role=Role.SYSTEM, timestamp_start=datetime.now(), content=result_message_str)
        state.conversation.append(result_message)
        return result

