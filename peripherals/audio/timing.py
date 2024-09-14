# Internal libs
from peripherals.audio.input import Input
from peripherals.audio.output import Output

from infra.resources_management.threaded_app import ThreadedApp

# General utilities
from time import sleep
from typing import List


class Timing(ThreadedApp):

    output_apps: List[Output]
    input_apps: List[Input]

    def __init__(self, input_apps: List[Input], output_apps: List[Output]):
        super().__init__()
        self.input_apps = input_apps
        self.output_apps = output_apps

        self._make_thread(self.__time_audio_inout)

    def __time_audio_inout(self):
        while not self.was_closed:
            if any(app.active() for app in self.output_apps):
                self._logger.debug("Active App detected")
                for app in self.input_apps:
                    app.stop_recording()
                sleep(1.0)
                for app in self.output_apps:
                    app.start_playing()
            else:
                self._logger.debug("No Active App detected")
                for app in self.output_apps:
                    app.stop_playing()
                sleep(1.0)
                for app in self.input_apps:
                    app.start_recording()
            sleep(1.0)


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup()

    from peripherals.audio.audio import Audio

    with Input() as inp:
        with Output() as output:
            with Timing([inp], [output]) as timing:
                for i in range(3):
                    record: Audio
                    _, record = inp.queue.get()
                    output.play(record)
                    sleep(1.0)
