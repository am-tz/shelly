# External libs
from pyaudio import PyAudio

from peripherals.audio.audio import Audio

# Internal libs
from infra.resources_management.threaded_app import ThreadedApp
from threading import Lock, Event
from typing import List, Tuple, Mapping

import speech_recognition as sr
from speech_recognition import Microphone, Recognizer
from datetime import datetime, timedelta
from queue import Queue


# TODO: Add average noise reset
class Input(ThreadedApp):

    CHUNK_SIZE: int = 4096

    __recognizer: Recognizer = None
    __record_flag: Event = None

    __mic_info: Mapping[str, str | int | float] = None

    __short_timeout_count: int = None
    __short_timeout_count_lock: Lock = None

    __listen_start_timestamp: datetime | None = None
    __listen_stop_timestamp: datetime | None = None
    __listen_start_timestamp_lock: Lock = None
    __listen_stop_timestamp_lock: Lock = None

    __long_timeout: float = None
    __short_timeout: float = None

    queue: Queue[Tuple[datetime, Audio]] = None

    def __init__(self, long_timeout: float = 10.0, short_timeout: float = 1.0):
        super().__init__()

        py_audio: PyAudio = PyAudio()
        preferred_mic = "USB PnP Sound Device: Audio (hw:3,0)"
        self.__mic_info = py_audio.get_default_input_device_info()

        device_names: List[str] = [device['name'] for device in
                                   [py_audio.get_device_info_by_index(i) for i in range(py_audio.get_device_count())]]

        if preferred_mic in device_names:
            self.__mic_info = py_audio.get_device_info_by_index(device_names.index(preferred_mic))
        self._logger.debug(f"Using Microphone: '{self.__mic_info['name']}'")

        self.__long_timeout = long_timeout
        self.__short_timeout = short_timeout
        self.__short_timeout_count = 0
        self.__short_timeout_count_lock = Lock()

        self.__listen_start_timestamp = None
        self.__listen_start_timestamp_lock = Lock()
        self.__listen_stop_timestamp_lock = Lock()
        self.__recognizer = Recognizer()
        self.__record_flag = Event()

        self.queue = Queue()
        self.__queue_lock = Lock()

        self._make_thread(self.__input_loop)

    def stop_recording(self) -> None:
        if self.__record_flag.is_set():
            with self.__listen_stop_timestamp_lock:
                self.__listen_stop_timestamp = datetime.now()
                self.__record_flag.clear()

    def start_recording(self) -> None:
        self.__record_flag.set()
        with self.__listen_stop_timestamp_lock:
            self.__listen_stop_timestamp = None

    def is_recording(self) -> bool:
        """
        This is an approximation: It actually indicates whether we have been recording for a sufficiently long time,
        i.e. for longer than the timeout of the corresponding listening attempt.
        :return: True if we are sure we are recording, else False.
        """
        audio_timestamp: datetime = self.__timestamp_thread_safe
        now_timestamp: datetime = datetime.now()
        if not audio_timestamp:
            return False

        timeout: float = self.__short_timeout if self.__short_timeout_count else self.__long_timeout
        return audio_timestamp + timedelta(seconds=timeout) < now_timestamp

    def start(self) -> None:
        super().start()
        self.start_recording()

    def close(self) -> None:
        self.__long_timeout = 0.01
        self.__short_timeout = 0.01
        self.start_recording()  # to get out of potential lock wait deadlock
        super().close()

    @property
    def __timestamp_thread_safe(self) -> datetime | None:
        with self.__listen_start_timestamp_lock:
            return self.__listen_start_timestamp

    @__timestamp_thread_safe.setter
    def __timestamp_thread_safe(self, val: datetime):
        with self.__listen_start_timestamp_lock:
            self.__listen_start_timestamp = val

    @property
    def __timestamp_stop_thread_safe(self) -> datetime | None:
        with self.__listen_stop_timestamp_lock:
            return self.__listen_stop_timestamp

    @__timestamp_stop_thread_safe.setter
    def __timestamp_stop_thread_safe(self, val: datetime):
        with self.__listen_stop_timestamp_lock:
            self.__listen_stop_timestamp = val

    @property
    def __short_timeout_count_thread_safe(self):
        with self.__short_timeout_count_lock:
            return self.__short_timeout_count

    @__short_timeout_count_thread_safe.setter
    def __short_timeout_count_thread_safe(self, val: int):
        with self.__short_timeout_count_lock:
            self.__short_timeout_count = val

    def __input_loop(self) -> None:
        with sr.Microphone(device_index=self.__mic_info['index']) as source:
            while not self.was_closed:
                self.__record_flag.wait()
                self._logger.debug("Starting to listen")
                self.__timestamp_thread_safe = datetime.now()
                source: Microphone
                try:
                    sr_audio: sr.AudioData
                    timeout: float = self.__short_timeout if self.__short_timeout_count else self.__long_timeout
                    sr_audio = self.__recognizer.listen(source, timeout)
                except sr.WaitTimeoutError:
                    self._logger.debug("Didn't hear anything")
                    self.__short_timeout_count_thread_safe = max(self.__short_timeout_count_thread_safe - 1, 0)
                    continue
                finally:
                    self.__timestamp_thread_safe = None

                audio = Audio(byte_chunks=[sr_audio.frame_data],
                              channels=1,
                              sample_width=sr_audio.sample_width,
                              frame_rate=sr_audio.sample_rate,
                              chunk_size=self.CHUNK_SIZE)

                if not self.__record_flag.is_set():
                    time = datetime.now()
                    spilled_time: float = (time - self.__timestamp_stop_thread_safe).total_seconds()
                    audio_time: float = audio.seconds()
                    if audio_time > spilled_time:
                        audio = audio.copy(end_time=audio_time - spilled_time)
                    else:
                        continue
                if audio.root_mean_square_energy() < 200:
                    continue

                self.queue.put((datetime.now()-timedelta(seconds=audio.seconds()), audio))
                self._logger.debug(f"Recorded {audio.seconds():.1f} seconds of audio.")
                self.__short_timeout_count_thread_safe = 3


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from peripherals.audio.output import Output
    from time import sleep
    with Input() as inp:
        with Output() as output:
            record: Audio
            _, record = inp.queue.get()
            reloaded_record: Audio = Audio(wav_buffer=record.stream())
            output.play(reloaded_record)
            sleep(reloaded_record.seconds())
