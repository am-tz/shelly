# External libs
import json

# Internal libs
from dynamics.state import State
from dynamics.task.interface.interface import Interface

from gpt.client import Client
from gpt.conversation import Conversation, Message
from gpt.role import Role
from gpt.model import Model

from infra.log.loggable import Loggable

# General utilities
from threading import Thread
from datetime import datetime
from os.path import join, pardir, dirname, realpath
from os import linesep
from typing import Dict, Set, Any


class Execution(Loggable):
    """
    Builds prompts and asks GPT to choose parameters for given tasks, given the intent expressed in the respective
    previous message. Then runs the given task with the chosen parameters.
    """

    __client: Client = None

    __prompt_front: str = None
    __prompt_mid: str = None
    __prompt_tail: str = None

    def __init__(self):

        super().__init__()

        directory: str = realpath(join(dirname(realpath(__file__)), pardir, pardir, "files", "system_prompts"))
        with open(join(directory, "execute_front.txt"), "r") as fh:
            self.__prompt_front = fh.read()

        with open(join(directory, "execute_mid.txt"), "r") as fh:
            self.__prompt_mid = fh.read()

        with open(join(directory, "execute_tail.txt"), "r") as fh:
            self.__prompt_tail = fh.read()

        self.__client = Client()

    def validate_json(self, gpt_output: str, interface: Interface) -> Dict[str, str]:
        warning_start: str = f"Could not execute task'{interface.name}': "
        try:
            parameter_dict: Dict[str, Any] = json.loads(gpt_output)
        except json.JSONDecodeError:
            self._logger.warning(f"{warning_start} invalid JSON in task execution response '{gpt_output}'")
            return {}

        if not all(isinstance(x, str) for x in parameter_dict.values()):
            self._logger.warning(f"{warning_start} invalid parameter dict {parameter_dict}")
            return {}

        output_parameter_names: Set[str] = set(parameter_dict.keys())
        correct_parameters: bool = output_parameter_names == set(interface.argument_names())
        unique_parameters: bool = len(output_parameter_names) == len(interface.argument_names())
        if not correct_parameters or not unique_parameters:
            self._logger.warning(f"{warning_start} invalid parameter dict {parameter_dict}")
            return {}

        return parameter_dict

    def __do(self, interface: Interface, state: State, kwargs: Dict[str, str]):

        task_result: Message | None = interface(**kwargs)
        task_name: str = interface.name
        if not task_result:
            task_result = Message(role=Role.SYSTEM,
                                  timestamp_start=datetime.now(),
                                  content=f"Could not execute task '{task_name}' with parameters {kwargs}")
            self._logger.warning(task_result)
        else:
            self._logger.info(f"Successfully executed task '{task_name}' with parameters {kwargs}")

        state.conversation.append(task_result)

    def do(self, interface: Interface, state: State) -> None:
        """
        Chooses parameters for a given task based on a given state, and executes it
        :param interface: interface class that executes the task
        :param state: A State instance
        :return: The chosen LLMInterface instance
        """

        # We only query GPT if the function actually has parameters
        parameter_dict: Dict[str, str] = {}
        if interface.argument_names():
            content: str = linesep.join([
                self.__prompt_front,
                state.env_info_string(),
                self.__prompt_mid,
                interface.doc,
                self.__prompt_tail
            ])

            system_message: Message = Message(role=Role.SYSTEM, content=content)
            thought = [msg for msg in state.conversation if msg.role == Role.ASSISTANT][-1]
            parameter_prompt: Conversation = system_message + interface.few_shot_examples() + thought

            gpt_output: str = self.__client.query_chat(parameter_prompt,
                                                       json_format=True,
                                                       temperature=0.1,
                                                       model=Model.GPT__4__1106__PREVIEW)

            self._logger.debug(f"Raw GPT output: '{gpt_output}'")
            parameter_dict = self.validate_json(gpt_output, interface)

        Thread(target=self.__do, args=(interface, state, parameter_dict)).start()
