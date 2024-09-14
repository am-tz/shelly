# External libs
from itertools import cycle

# Internal libs
from dynamics.task.interface.interface import Interface, Message
from peripherals.wheels.move import Direction, Speed, Move as MoveImp
from gpt.role import Role

# General utilities
from datetime import datetime
from typing import List


class ShakeHead(Interface):
    """
    ShakeHead: Allows you to shake your head as often as you want to, with a given intensity
    """

    __move_imp: MoveImp = None

    __max_number_of_times: int = None
    __max_turn_seconds: float = None

    def __init__(self, move_imp: MoveImp, max_number_of_times: int = 20, max_turn_seconds: float = 1.0):

        super().__init__()

        self.__move_imp = move_imp

        self.__max_number_of_times = max_number_of_times
        self.__max_turn_seconds = max_turn_seconds

    def __call__(self, number_of_times: int, magnitude: float) -> Message | None:
        """
        This function lets Shelly shake his head a given number of times. For example,

        2
        0.5

        means shaking the head twice, once to each side, with medium magnitude. Another example:

        10
        0.1

        means shaking the head ten times in total, with a small magnitude.

        Since Shelly does not actually have a movable head, it shakes its whole body instead by consecutively
        turing left and right for several times. Since there is only one speed setting for Shelly, the turns that
        emulate the headshakes will have the same speed regardless of

        :param number_of_times: How many times the head is shaken, and integer value
        :param magnitude: A float value strictly between 0.0 and 1.0, that determines the magnitude of the head shake.
        :return: A log message corresponding to the movement, or None if parsing the input failed.
        """

        try:
            number_of_times_int = int(number_of_times)
        except ValueError:
            return None

        if number_of_times_int > self.__max_number_of_times or number_of_times_int <= 0.0:
            return None

        try:
            magnitude_float = float(magnitude)
        except ValueError:
            return None

        if not 0.0 < magnitude_float < 1.0:
            return None

        shakes: cycle[Direction] = cycle([Direction.LEFT, Direction.RIGHT])
        directions: List[Direction] = [direction for direction, i in zip(shakes, range(number_of_times_int))]
        speeds: List[Speed] = [Speed.STILL] * number_of_times_int
        times: List[float] = [magnitude_float * self.__max_turn_seconds] * number_of_times_int

        start_time: datetime = datetime.now()
        log_text: str = self.__move_imp.move_sequence(directions, speeds, times)
        if not log_text:
            return None
        end_time: datetime = datetime.now()
        return Message(role=Role.SYSTEM, content=log_text, timestamp_start=start_time, timestamp_end=end_time)


if __name__ == '__main__':
    print(ShakeHead.__call__.__doc__)
