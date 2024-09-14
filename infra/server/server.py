# External libs
from werkzeug.serving import make_server, BaseWSGIServer

# Internal libs
from infra.server import HOST, PORT
from infra.server.app import App, MoveImp, ChatQueues

from infra.resources_management.manager import Manager
from infra.resources_management.manageable_wrapper import ManageableWrapper

# External libs
from threading import Thread


class Server(Manager):
    """
    Wrapper around a werkzeug server running the flask app
    """

    __server: BaseWSGIServer = None
    __thread: Thread = None

    def __init__(self, move_implementation: MoveImp, queues: ChatQueues, host: str = None, port: str = None):

        super().__init__()

        self.__host = host or HOST
        self.__port = port or PORT

        if self.__host == 'localhost':
            self._logger.exception("Workaround to get local IP failed")

        self._logger.info(f"Starting server at {self.__host}:{PORT}")

        self.__server = make_server(self.__host, self.__port, App(move_implementation, self._was_closed, queues).app)
        self.__thread = Thread(target=self.__server.serve_forever)
        self.register(ManageableWrapper(like_start=self.__thread.start, like_close=self.__server.shutdown))

    @property
    def ip(self) -> str:
        return self.__server.server_address[0]


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from sys import argv

    custom_host: str = argv[1] if len(argv) > 1 else None
    custom_port: str = argv[2] if len(argv) > 2 else None

    with Server(MoveImp(), ChatQueues(), host=custom_host, port=custom_port) as manager:
        from time import sleep
        while not manager.was_closed:
            sleep(1.0)
            pass
