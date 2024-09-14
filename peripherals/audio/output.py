# External libs
from pyaudio import PyAudio, Stream

from peripherals.audio.audio import Audio

# Internal libs
from infra.resources_management.threaded_app import ThreadedApp
from threading import Lock, Event
from typing import List, Dict, Tuple


class Output(ThreadedApp):

    __py_audio: PyAudio = None

    __queue: List[Audio] = None
    __queue_lock: Lock = None
    __play_flag: Event = None

    __streams: Dict[Tuple[int, int, int], Stream] = None

    def __init__(self):
        super().__init__()

        self.__queue = []
        self.__queue_lock = Lock()
        self.__play_flag = Event()

        self.__streams = {}
        self.__py_audio = PyAudio()

        self._make_thread(self.__output_loop)

    def stop_playing(self):
        self.__play_flag.clear()

    def start_playing(self):
        self.__play_flag.set()

    def active(self):
        with self.__queue_lock:
            return bool(self.__queue)

    def clear(self):
        with self.__queue_lock:
            self.__queue.clear()

    def play(self, audio: Audio, prioritise: bool = False):
        with self.__queue_lock:
            self._logger.debug(f"Adding audio to queue {'start' if prioritise else 'end'}")
            self.__queue.insert(0 if prioritise else len(self.__queue), audio)

    def __chunk(self):
        with self.__queue_lock:
            while self.__queue:
                if not self.__queue[0].chunks:
                    self.__queue.pop()
                else:
                    return self.__queue[0].pop()
            return None

    def __get_stream(self, sample_width: int, channels: int, frame_rate: int) -> Stream:
        """
        This is not efficient if there are many formats, but the caller can standardise the input if they want
        :param sample_width: Width of each frame in bytes
        :param channels: Number of channels
        :param frame_rate: Frames per second
        :return: An output stream that works for audio corresponding to the input parameters
        """
        key: Tuple[int, int, int] = (sample_width, channels, frame_rate)
        if key not in self.__streams:
            stream: Stream = self.__py_audio.open(
                format=self.__py_audio.get_format_from_width(sample_width),
                channels=channels,
                rate=frame_rate,
                output=True
            )
            self.__streams[key] = stream

        return self.__streams[key]

    def __play(self, audio: Audio) -> None:
        audio.to_standard_width()

        stream: Stream = self.__get_stream(audio.sample_width, audio.channels, audio.frame_rate)
        for chunk in audio.chunks:
            stream.write(chunk.tobytes())

    def __output_loop(self) -> None:
        while not self.was_closed:
            self.__play_flag.wait()
            audio_chunk: Audio = self.__chunk()
            if audio_chunk:
                self.__play(audio_chunk)

    def start(self) -> None:
        super().start()
        self.start_playing()

    def close(self) -> None:
        super().close()
        self.start_playing()  # to get out of potential lock wait deadlock
        stream: Stream
        for _, stream in self.__streams.items():
            stream.close()
        self.__py_audio.terminate()


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from os.path import join, realpath, pardir, dirname
    from time import sleep

    obj: Audio = Audio(wav_filename=join(realpath(dirname(__file__)), pardir, pardir, "files", "tests", "bam.wav"))
    with Output() as output:
        output.play(obj)
        sleep(obj.seconds())
