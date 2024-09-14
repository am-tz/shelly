# Internal libs
from dynamics.task.interface.interface import Interface
from peripherals.audio.output import Output, Audio
from gpt.client import Client
from gpt.role import Role
from gpt.message import Message

# General utilities
from datetime import datetime, timedelta


class Speak(Interface):
    """
    Speak: Allows you to say something out loud
    """

    __output: Output
    __client: Client

    def __init__(self, output: Output):

        super().__init__()

        self.__output = output
        self.__client = Client(1.0)

    def __call__(self, text: str) -> Message | None:
        """
        This function lets Shelly speak via its loudspeakers and text to speech. There is just one parameter, the string
        that is supposed to be spoken. This parameter is referred to as 'text'.

        :param text: The text that is going to be spoken
        :type: str
        :return: A log message containing the content of the 'text' parameter.
        """

        audio: Audio = self.__client.query_tts(text)
        self.__output.play(audio)
        time = datetime.now()
        return Message(role=Role.USER,
                       content=text,
                       name="Shelly",
                       language=self.__client.language,
                       timestamp_start=time,
                       timestamp_end=time + timedelta(seconds=audio.seconds()))


if __name__ == '__main__':
    print(Speak.__call__.__doc__)
