# Internal Libs
from peripherals.wheels.enums.direction import Direction
from peripherals.wheels.enums.speed import Speed
from peripherals.wheels.enums.side import Side
from peripherals.wheels.gpio import GPIO

from infra.resources_management.manager import Manager

# General utilities
from time import sleep
from os import linesep
from typing import List


class Move(Manager):

    __motor_controller_instructions = {
        Speed.STILL: [GPIO.LOW, GPIO.LOW],
        Speed.FORWARD: [GPIO.HIGH, GPIO.LOW],
        Speed.BACKWARD: [GPIO.LOW, GPIO.HIGH],
    }

    used_gpio_pins = None
    pin_status = None

    def __init__(self):

        super().__init__()

        GPIO.setmode(GPIO.BOARD)
        self.used_gpio_pins = [7, 11, 13, 15]
        self.pin_status = [GPIO.LOW] * 4

        GPIO.setup(self.used_gpio_pins, GPIO.OUT, initial=GPIO.LOW)

    def close(self):
        super().close()
        GPIO.cleanup()

    def __set(self, pin_indices, values):
        for pin_index, value in zip(pin_indices, values):
            GPIO.output(self.used_gpio_pins[pin_index], value)
            self.pin_status[pin_index] = value

    def __move_side(self, side, speed):
        pin_indices = [0, 1] if side == Side.LEFT else [2, 3]
        self.__set(pin_indices, self.__motor_controller_instructions[speed])

    def __move(self, direction, active_speed, inactive_speed=None):
        if direction == Direction.STRAIGHT:
            self.__move_side(Side.LEFT, active_speed)
            self.__move_side(Side.RIGHT, active_speed)
        else:
            active_side = Side.LEFT if direction == Direction.RIGHT else Side.RIGHT
            inactive_side = Side.RIGHT if active_side == Side.LEFT else Side.LEFT
            self.__move_side(active_side, active_speed)
            self.__move_side(inactive_side, inactive_speed)

    def start_move(self, direction, speed) -> str:
        if speed == Speed.STILL and direction == Direction.STRAIGHT:
            log_message: str = "Stopped moving"
            self.__move(direction, Speed.STILL)
        elif speed == Speed.STILL:
            self.__move(direction, Speed.FORWARD, Speed.BACKWARD)
            log_message: str = f"Turning {direction.name.lower()}"
        else:
            log_message: str = f"Moving {direction.name.lower()} {speed.name.lower()}"
            self.__move(direction, speed, Speed.STILL)
        self._logger.info(log_message)
        return log_message

    def move(self, direction, speed, seconds) -> str:
        log_message: List[str] = [self.start_move(direction, speed)]
        wait_message: str = f".. for {seconds:.1f} seconds"
        log_message.append(wait_message)
        self._logger.info(wait_message)
        sleep(seconds)
        log_message.append(self.start_move(Direction.STRAIGHT, Speed.STILL))
        return linesep.join(log_message)

    def move_sequence(self, directions, speeds, seconds_list) -> str:
        log_messages: List[str] = []
        for direction, speed, seconds in zip(directions, speeds, seconds_list):
            log_message: str = self.start_move(direction, speed)
            log_messages.append(log_message)
            wait_message: str = f".. for {seconds:.1f} seconds"
            log_messages.append(wait_message)
            self._logger.info(wait_message)
            sleep(seconds)
            log_message = self.start_move(Direction.STRAIGHT, Speed.STILL)
            log_messages.append(log_message)
        return linesep.join(log_messages)
