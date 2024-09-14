# External libs

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest

# General utils
from threading import Event


class ExitRequest(BaseEndPointRequest):

    __flag: Event = None

    def __init__(self, exit_flag: Event):
        self.__flag = exit_flag

    def __shutdown_server(self) -> None:
        self.__flag.set()

    def get(self) -> str:
        self.__flag.set()
        return "Initiated server shutdown"

    @staticmethod
    def endpoint():
        return "exit"
