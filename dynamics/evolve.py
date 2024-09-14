# Internal libs
from task.interface.interface import Interface
from task.interface.move import Move, MoveImp
from task.interface.shake_head import ShakeHead
from task.interface.speak import Speak
from task.interface.ponder import Ponder

from dynamics.state import State
from dynamics.task.thought import Thought
from dynamics.task.choice import Choice
from dynamics.task.execution import Execution

from gpt.langauge import Language
from gpt.conversation import Conversation
from gpt.message import Message

from peripherals.audio.input import Input as AudioInput
from peripherals.audio.output import Output as AudioOutput
from peripherals.audio.timing import Timing as AudioTiming
from peripherals.audio.apps.white_noise_generator import WhiteNoiseGenerator
from peripherals.audio.apps.transcription_generator import TranscriptionGenerator
from peripherals.text.chat_queues import ChatQueues

from infra.server.server import Server

from peripherals.temperature.cpu import Cpu

from infra.resources_management.manager import Manager

# General utilities
from time import sleep
from datetime import datetime
from typing import List

from os import system


# TODO: Github
# TODO: Migrate to librosa
# TODO: Improve audio input
# TODO: Add vision
# TODO: Add __main__.py
# TODO: Add task queue? Maybe we don't need it
# TODO: Implement shelly's choose thoughts
# TODO: Implement Speech interface - won't need any parameters
# TODO: Actually use the conversation pruning functionality somewhere
# TODO: Implement Soundboard interface - could be tricky to get parameters working in a generic way
# TODO: Add short description to BaseTaskInterface to use in General Info Section
# TODO: Make Shelly aware of whether it is being moved or if it moved autonomously
class Evolve(Manager):
    """
    Main class: Creates and transitions between states, and manages all resources needed to do so
    """

    # Resources
    __move_imp: MoveImp = None
    __audio_input: AudioInput = None
    __audio_output: AudioOutput = None
    __audio_timing: AudioTiming = None
    __transcription_generator: TranscriptionGenerator = None
    __chat_queues: ChatQueues = None
    __white_noise_generator: WhiteNoiseGenerator = None
    __server_manager: Server = None
    __cpu_temp_check: Cpu = None

    # user-selected state variables
    __language: Language = None

    # conversation history
    __conversation: Conversation = None

    # available interfaces
    __shelly_interfaces: List[Interface] = None

    # Dynamics parts
    __thought: Thought = None
    __choice: Choice = None
    __execution: Execution = None

    def __init__(self, language: Language = Language.EN):

        super().__init__()

        # Manageable types
        self.__move_imp = self.register(MoveImp())
        # Audio input is disabled for now because of microphone issues
        # self.__audio_input = self.register(AudioInput(long_timeout=6.0))
        self.__audio_output = self.register(AudioOutput())
        self.__audio_timing = self.register(AudioTiming([], [self.__audio_output]))
        # self.__transcription_generator = self.register(TranscriptionGenerator(self.__audio_input, 10.0))
        self.__chat_queues = self.register(ChatQueues())
        self.__white_noise_generator = self.register(WhiteNoiseGenerator())
        self.__server_manager = self.register(Server(self.__move_imp))
        self.__cpu_temp_check = self.register(Cpu())

        self.__language = language

        self.__conversation = Conversation([])

        self.__shelly_interfaces = [
            Move(self.__move_imp),
            ShakeHead(self.__move_imp),
            Speak(self.__audio_output),
            Ponder()
        ]

        self.__thought = Thought(self.__shelly_interfaces)
        self.__choice = Choice(self.__shelly_interfaces)
        self.__execution = Execution()

    def run(self) -> None:
        while not self.was_closed:
            self.__thought.think(self.state)
            action: Interface = self.__choice.make(self.state)
            if action:
                self.__execution.do(action, self.state)

            sleep(10.0)

    @property
    def state(self) -> State:
        #        while self.__transcription_generator.queue.qsize() > 0:
        #            message: Message = self.__transcription_generator.queue.get
        while self.__chat_queues.input_queue.qsize() > 0:
            message: Message = self.__chat_queues.input_queue.queue.get()
            self._logger.info(message)
            self.__conversation.append(message)

        return State(self.__time, self.__language, self.__cpu_temperature, self.__conversation)

    @property
    def __time(self) -> datetime:
        return datetime.now()

    @property
    def __cpu_temperature(self) -> float | None:
        return self.__cpu_temp_check.temperature


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup

    LoggingSetup(LoggingSetup.INFO)

    from time import sleep

    with Evolve() as evolve:
        evolve.run()
        sleep(20)
