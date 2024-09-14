# External libs
from flask import Flask
from flask_restful import Api

# Internal libs
from infra.server.requests.utils import add_resource
from infra.server.requests.home_request import HomeRequest
from infra.server.requests.move_request import MoveRequest, Move as MoveImp
from infra.server.requests.exit_request import ExitRequest
from infra.server.requests.shutdown_request import ShutdownRequest

# General utilities
from threading import Event


class App:

    @property
    def app(self):
        return self.__app

    __app: Flask = None
    __api: Api = None

    def __init__(self, move_implementation: MoveImp, exit_flag: Event):
        self.__app = Flask(__name__)
        self.__api = Api(self.app)

        add_resource(self.__api, HomeRequest)
        add_resource(self.__api, MoveRequest, move_implementation=move_implementation)
        add_resource(self.__api, ExitRequest, exit_flag=exit_flag)
        add_resource(self.__api, ShutdownRequest)


if __name__ == '__main__':
    App(MoveImp(), Event()).app.run(debug=True)
