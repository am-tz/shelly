# Internal libs
from gpt.message import Message
from gpt.role import Role
from gpt.langauge import Language

from infra.resources_management.manageable_wrapper import ManageableWrapper

# General utilities
from datetime import datetime
from queue import Queue, Empty


class ChatQueues(ManageableWrapper):

    input_queue: Queue[Message] = None
    output_queue: Queue[Message] = None
    language: Language = Language.EN

    def __init__(self):

        super().__init__()

        self.input_queue = Queue()
        self.output_queue = Queue()

    def put_input_message(self, text: str, language: Language = Language.EN):
        self.language = language
        message: Message = Message(role=Role.USER,
                                   content=text,
                                   language=language,
                                   timestamp_start=datetime.now(),
                                   timestamp_end=datetime.now())

        try:
            self.input_queue.put(message, True, 0.1)
            self._logger.info(f"Received text input: {message.content}")
        except Empty:
            self._logger.exception("Could not put message into queue (queue is unexpectedly blocked)")

    def put_output_message(self, message: Message):
        try:
            self.output_queue.put(message, True, 0.1)
            self._logger.info(f"Put text output: {message.content}")
        except Empty:
            self._logger.exception("Could not put message into queue (queue is unexpectedly blocked)")
