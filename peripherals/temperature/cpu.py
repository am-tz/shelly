# Internal libs
from infra.resources_management.threaded_app import ThreadedApp

# General utilities
from subprocess import run, CompletedProcess
from re import Pattern, compile
from time import sleep


class Cpu(ThreadedApp):
    """
    Continuously measures CPU temperature on a raspberry pi
    """

    temperature: float | None = None

    __refresh_rate: float = None

    __command: str = None
    __pattern: Pattern = None

    def __init__(self, refresh_rate_in_seconds: float = 10.0):

        super().__init__()

        self.__command = "/usr/bin/vcgencmd measure_temp"
        self.__pattern = compile(r"temp=(\d+\.\d+)'C")

        self.__refresh_rate = refresh_rate_in_seconds
        self._make_thread(self.__update)

    def __measure_temp(self) -> float | None:
        proc: CompletedProcess = run(self.__command, capture_output=True, shell=True, encoding="utf-8")
        match = self.__pattern.match(proc.stdout)
        if match:
            self.temperature = float(match[1])
        else:
            self.temperature = None

        return self.temperature

    def __update(self) -> None:
        while not self.was_closed:
            self.temperature = self.__measure_temp()
            if self.temperature:
                self._logger.info(f"CPU Temperature measured at {self.temperature:.1f}'C")
            else:
                self._logger.warning("Could not measure CPU temperature")
            sleep(self.__refresh_rate)


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    with Cpu(2.0) as cpu_temp:
        sleep(1.0)
        temp = cpu_temp.temperature
        if temp:
            print(f"CPU temp is at {cpu_temp.temperature:.1f}'C")
        else:
            print("CPU temp could not be measured")
