# Internal libs
from gpt.langauge import Language
from gpt.conversation import Conversation

# General utilities
from datetime import datetime
from os import linesep


class State:
    """
    Represents a state of the robot, including current environment information and a history of the conversation so far
    """

    # Environment info
    time: datetime = None
    language: Language = None
    cpu_temperature: float | None = None

    # Conversation history
    conversation: Conversation = None

    def __init__(self,
                 time: datetime,
                 language: Language,
                 cpu_temperature: float | None,
                 conversation: Conversation):

        self.time = time
        self.language = language
        self.cpu_temperature = cpu_temperature

        self.conversation = conversation

    @property
    def datetime_string(self) -> str:
        return f"Current date and time: '{self.time:%y-%m-%d--%H-%M-%S}"

    @property
    def language_string(self) -> str:
        return f"The current language is set to: {self.language.name}"

    @property
    def cpu_temperature_string(self) -> str:
        if self.cpu_temperature:
            return f"CPU temperature on raspberry pi: f{self.cpu_temperature}'C"
        else:
            return f"Could not measure CPU temperature on raspberry pi."

    def env_info_string(self) -> str:
        return linesep.join([self.datetime_string,
                             self.language_string,
                             self.cpu_temperature_string])
