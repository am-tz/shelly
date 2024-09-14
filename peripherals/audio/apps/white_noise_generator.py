# External libs

# Internal libs
from peripherals.audio.output import Output, Audio

from infra.resources_management.threaded_app import ThreadedApp

# General utilities
from time import sleep
from os.path import join, pardir, dirname, realpath


class WhiteNoiseGenerator(ThreadedApp):

    __output: Output = None
    __audio: Audio = None

    def __init__(self):

        super().__init__()

        self.__output = Output()

        self._logger.debug("Setting directories..")
        directory: str = dirname(realpath(__file__))
        wav_path: str = realpath(join(directory, pardir, pardir, pardir, "files", "other", "whitenoise.wav"))
        self.__audio = Audio(wav_filename=wav_path)

        self._make_thread(self.__white_noise)

    def __white_noise(self) -> None:
        while not self.was_closed:
            self.__output.play(self.__audio.copy())
            sleep(self.__audio.seconds())

    def start(self) -> None:
        super().start()
        self.__output.start()

    def close(self) -> None:
        super().close()
        self.__output.close()


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from time import sleep
    with WhiteNoiseGenerator() as wng:
        wng.start()
        sleep(3.0)
