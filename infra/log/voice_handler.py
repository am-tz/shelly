# Internal libs
import logging

from peripherals.audio.apps.espeak import ESpeak
from peripherals.audio.enums.espeak_mode import EspeakMode
from peripherals.audio.audio import Audio
from peripherals.audio.output import Output

from gpt.langauge import Language

# General utilities
from time import sleep
from threading import Thread
from logging import Handler, LogRecord


class VoiceHandler(Handler):

    __espeak: ESpeak = None
    __output: Output = None

    language: Language = None
    mode: EspeakMode = None

    def __init__(self, in_out: Output, level: int, language: Language = Language.EN, mode: EspeakMode = None):
        super().__init__(level)
        self.__espeak = ESpeak()
        self.__output = in_out
        self.language = language
        self.mode = mode

    def play(self, text: str) -> None:
        audio: Audio = self.__espeak.tts(text, self.language, self.mode)
        self.__output.clear()
        self.__output.play(audio)
        self.__output.start_playing()
        sleep(audio.seconds())

    def emit(self, record: LogRecord) -> None:
        # Do this in a separate thread since entering this method acquires a thread lock in the logging class
        # -> Could be deadlocked
        Thread(target=self.play, args=[record.getMessage()]).start()
