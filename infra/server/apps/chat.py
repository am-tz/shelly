# External libs
from time import sleep

# Internal libs
from infra.server.client import Client
from infra.log.loggable import Loggable
from infra.server.app import ChatQueues
# General utilities


class Chat(Loggable):

    __rest_client: Client = None

    def __init__(self, custom_host: str):

        super().__init__()

        self.__rest_client = Client(host=custom_host)

    def run(self) -> None:
        self._logger.info("Entered chat mode.. Write 'exit()' to exit.")

        message: str = ""
        while not message == "exit()":
            message = input()
            self.__rest_client.put_message(message, "EN")
            sleep(10.0)
            self.__rest_client.get_messages()

        self._logger.info("Exited chat mode..")


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup

    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from infra.server.server import Server
    from peripherals.wheels.move import Move
    from sys import argv

    host = argv[1] if len(argv) > 1 else 'localhost'

    if host == 'localhost':
        with Server(Move(), ChatQueues(), host=host) as manager:
            cm = Chat(manager.ip)
            cm.run()
    else:
        cm = Chat(host)
        cm.run()
