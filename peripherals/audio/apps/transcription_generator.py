# Internal libs
from peripherals.audio.audio import Audio
from peripherals.audio.input import Input

from gpt.client import Client
from gpt.message import Message
from gpt.role import Role
from gpt.langauge import Language

from infra.resources_management.threaded_app import ThreadedApp

# General utilities
from datetime import datetime, timedelta
from queue import Queue, Empty


class TranscriptionGenerator(ThreadedApp):

    __input: Input = None
    __client: Client = None

    recording_time: float = None

    queue: Queue[Message] = None

    @property
    def language(self) -> Language:
        return self.__client.language

    @language.setter
    def language(self, val: Language) -> None:
        self.__client.language = val

    def __init__(self, input_loop: Input, queue_timeout: float = 0.5):

        super().__init__()

        self.__input = input_loop
        self.__client = Client(0.5)

        self.__audios_queue = Queue()
        self.queue = Queue()
        self.__queue_timeout: float = queue_timeout

        self._make_thread(self.__transcription_loop)

    def __transcription_loop(self) -> None:
        audio: Audio | None = None
        while not self.was_closed:
            timestamp: datetime | None = None
            try:
                new_audio: Audio | None
                timestamp, new_audio = self.__input.queue.get(timeout=self.__queue_timeout)
            except Empty:
                new_audio = None

            if audio and new_audio:
                audio += new_audio
            elif new_audio:
                audio = new_audio
            else:
                continue

            # TODO: Recognise and add name
            # TODO: Stitch audios together with a pause
            transcription_text: str = self.__client.query_whisper(audio)

            if self.__input.is_recording():
                # Discard transcription and keep listening
                continue

            message: Message = Message(role=Role.USER,
                                       content=transcription_text,
                                       language=self.language,
                                       timestamp_start=timestamp,
                                       timestamp_end=timestamp+timedelta(seconds=audio.seconds()))

            try:
                self.queue.put(message, timeout=self.__queue_timeout)
                self._logger.info(f"Transcribed: {message.content}")
            except Empty:
                self._logger.exception("Could not put transcription into queue (queue is unexpectedly blocked)")


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.INFO)

    from time import sleep
    with Input() as inp:
        with Client() as client:
            with TranscriptionGenerator(inp, 2.0) as tgen:
                sleep(30.0)
                while tgen.queue.qsize() > 0:
                    print(tgen.queue.get(timeout=1.0).data)
