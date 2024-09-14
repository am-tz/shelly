# External libs
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

# Internal libs
from peripherals.wheels.move import Speed, Direction

from infra.server.client import Client

from infra.log.loggable import Loggable

# General utilities
from enum import Enum, auto
from typing import Dict


class ArrowKey(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


ArrowKeyDict: Dict[Key | KeyCode, ArrowKey] = {
    Key.up: ArrowKey.UP,
    Key.down: ArrowKey.DOWN,
    Key.left: ArrowKey.LEFT,
    Key.right: ArrowKey.RIGHT,
    KeyCode.from_char('w'): ArrowKey.UP,
    KeyCode.from_char('s'): ArrowKey.DOWN,
    KeyCode.from_char('a'): ArrowKey.LEFT,
    KeyCode.from_char('d'): ArrowKey.RIGHT,
    KeyCode.from_char('W'): ArrowKey.UP,
    KeyCode.from_char('S'): ArrowKey.DOWN,
    KeyCode.from_char('A'): ArrowKey.LEFT,
    KeyCode.from_char('D'): ArrowKey.RIGHT
}


class Steering(Loggable):

    __pressed: Dict[ArrowKey, bool] = None

    __rest_client: Client = None

    __speed_dict: Dict[int, Speed] = {
        -1: Speed.BACKWARD,
        0: Speed.STILL,
        1: Speed.FORWARD
    }

    __speed_score_dict: Dict[ArrowKey, int] = {
        ArrowKey.UP: 1,
        ArrowKey.DOWN: -1
    }

    __direction_dict: Dict[int, Direction] = {
        -1: Direction.LEFT,
        0: Direction.STRAIGHT,
        1: Direction.RIGHT
    }

    __direction_score_dict: Dict[ArrowKey, int] = {
        ArrowKey.LEFT: -1,
        ArrowKey.RIGHT: 1
    }

    def __init__(self, host: str):

        super().__init__()

        self.__rest_client = Client(host=host)

        self.__pressed = {
            ArrowKey.UP: False,
            ArrowKey.DOWN: False,
            ArrowKey.LEFT: False,
            ArrowKey.RIGHT: False
        }

    def __on_press(self, key: Key | KeyCode) -> bool:
        if (key == Key.esc) | (key == KeyCode.from_char('q')) | (key == KeyCode.from_char('Q')):
            return False
        elif key not in ArrowKeyDict:
            return True

        parsed_key = ArrowKeyDict[key]
        if not self.__pressed[parsed_key]:
            self._logger.debug(f"{parsed_key} pressed")
            self.__pressed[parsed_key] = True
            self.__move()
        return True

    def __on_release(self, key: Key | KeyCode) -> bool:
        if key not in ArrowKeyDict:
            return True

        parsed_key = ArrowKeyDict[key]
        if self.__pressed[parsed_key]:
            self._logger.debug(f"{parsed_key} released")
            self.__pressed[parsed_key] = False

            self.__move()
        return True

    def __move(self) -> None:
        self.__direction_score = sum(self.__direction_score_dict.get(k, 0) for k, v in self.__pressed.items() if v)
        self.__speed_score = sum(self.__speed_score_dict.get(k, 0) for k, v in self.__pressed.items() if v)

        direction = self.__direction_dict[self.__direction_score]
        speed = self.__speed_dict[self.__speed_score]
        self.__rest_client.move(direction, speed)

    def run(self) -> None:
        self._logger.info("Entered remote steering mode..")
        with keyboard.Listener(
                on_press=self.__on_press,
                on_release=self.__on_release,
                suppress=True) as listener:
            listener.join()
        self._logger.info("Exited remote steering mode..")


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup

    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from infra.server.server import Server
    from peripherals.wheels.move import Move
    from sys import argv

    host = argv[1] if len(argv) > 1 else 'localhost'

    if host == 'localhost':
        with Move() as move:
            with Server(move, custom_host=host) as manager:
                sm = Steering(manager.ip)
                sm.run()
    else:
        sm = Steering(host)
        sm.run()
