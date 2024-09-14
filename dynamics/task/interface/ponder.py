# Internal libs
from dynamics.task.interface.interface import Interface
from gpt.role import Role
from gpt.langauge import Language
from gpt.message import Message

# General utilities
from datetime import datetime


class Ponder(Interface):
    """
    Ponder: Allows you think for yourself for a bit
    """

    def __init__(self):

        super().__init__()

    def __call__(self) -> Message | None:
        """
        Does not have any parameters, does not need a description.

        :return: A log message saying that we want to ponder.
        """

        time = datetime.now()
        return Message(role=Role.SYSTEM,
                       content="You decided to ponder for a bit",
                       language=Language.EN,
                       timestamp_start=time)


if __name__ == '__main__':
    print(Ponder.__call__.__doc__)
