# Internal libs
from gpt.conversation import Conversation
from gpt.message import Message

from infra.log.loggable import Loggable

# General utilities
from abc import abstractmethod
from typing import List


class Interface(Loggable):
    """
    A base class for interfaces, providing the LLM with the ability to execute a task predefined task on the robot.
    To work properly, the __call__ method must have a detailed doc string, since it is used to explain the function
    to the LLM. Similarly, the class itself must have a short summary of what the class does - LIMIT THIS TO ONE LINE!
    Also, it is recommended to make few_shot_examples return some example usages.
    """

    @abstractmethod
    def __call__(self, *args, **kwargs) -> Message | None:
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def doc(self) -> str:
        return self.__call__.__doc__

    @property
    def summary(self) -> str:
        return self.__class__.__doc__

    @staticmethod
    def few_shot_examples() -> Conversation | None:
        """
        Override this function to run the task in few-shot mode
        :return: A conversation of alternating example request and reply messages for this task
        """
        return Conversation([])

    def argument_names(self) -> List[str]:
        return self.__call__.__code__.co_varnames[1:self.__call__.__code__.co_argcount]
