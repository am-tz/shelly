# Internal libs
from dynamics.task.interface.interface import Interface, Message
from peripherals.wheels.move import Direction, Speed, Move as MoveImp

# General utilities
from datetime import datetime
from gpt.role import Role


class Move(Interface):
    """
    Move: Allows you to move into a specific direction with a given speed, for a given time
    """

    __move_imp: MoveImp = None

    __max_move_time: float = None

    def __init__(self, move_imp: MoveImp, max_move_time: float = 60.0):

        super().__init__()

        self.__move_imp = move_imp
        self.__max_move_time = max_move_time

    def __call__(self, direction: str, speed: str, time: str) -> Message | None:
        """
        This function moves Shelly into a given way for a given time. For example,

        LEFT
        STILL
        3.0

        means an in-place left turn for three seconds. Another example:

        STRAIGHT
        BACKWARD
        1.0

        means moving straight backwards for one second.

        One full turn takes about 4 seconds, but it's not that exact.

        :param direction: One of the three direction strings "LEFT", "RIGHT", or "STRAIGHT"
        :param speed: One of the three speeds "FORWARD", "BACKWARD", or "STILL"
        :param time: Total time of the movement in seconds (can be float)
        :return: A log message corresponding to the movement, or None if parsing the input failed.
        """

        if direction in [x.name for x in Direction]:
            direction_enum = Direction[direction]
        else:
            return None

        if speed in [x.name for x in Speed]:
            speed_enum = Speed[speed]
        else:
            return None

        try:
            time_float = float(time)
        except ValueError:
            return None

        if time_float > self.__max_move_time or time_float <= 0.0:
            return None

        start_time = datetime.now()
        log_text: str = self.__move_imp.move(direction_enum, speed_enum, time_float)
        if not log_text:
            return None
        end_time: datetime = datetime.now()
        return Message(role=Role.SYSTEM, content=log_text, timestamp_start=start_time, timestamp_end=end_time)


if __name__ == '__main__':
    print(Move.__call__.__doc__)
