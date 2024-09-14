# External libs
from requests import get, post, Response

# Internal libs
from infra.server import HOST, PORT
from infra.server.requests.utils import pack_enums
from peripherals.wheels.enums.direction import Direction
from peripherals.wheels.enums.speed import Speed

from infra.log.loggable import Loggable


class Client(Loggable):

    __base_url: str = None

    def __init__(self, host: str = HOST, port: int = PORT):

        super().__init__()

        self.__base_url = f"http://{host}:{port}"

    def move(self, direction: Direction, speed: Speed):
        response: Response = post(f"{self.__base_url}/move", json=pack_enums(direction, speed))
        message = f"{response.status_code}: {response.text}"
        if response.status_code == 200:
            self._logger.info(message)
        else:
            self._logger.error(message)

    def put_message(self, user_message: str, language: str):
        response: Response = post(f"{self.__base_url}/textInput", json={'Message': user_message, 'Language': language})
        message = f"{response.status_code}: {response.text}"
        if response.status_code == 200:
            self._logger.info(message)
        else:
            self._logger.error(message)

    def get_messages(self):
        response: Response = get(f"{self.__base_url}/textOutput")
        message = f"{response.status_code}: {response.text}"
        if response.status_code == 200:
            self._logger.info(message)
        else:
            self._logger.error(message)


if __name__ == '__main__':
    from infra.server.server import Server
    from peripherals.wheels.move import Move

    with Server(Move()) as manager:
        Client().move(Direction.LEFT, Speed.STILL)
