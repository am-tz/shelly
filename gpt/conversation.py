# Internal libs
from gpt.message import Message

# General utilities
from copy import copy
from threading import Lock
from typing import List, Dict, Any


# TODO: Make cut_front smarter. We could add a summary of the conversation history instead of just removing messages.
class Conversation:
    """
    A wrapper around the message list used in the OpenAI API, that counts tokens and cuts off messages if necessary
    """

    @property
    def data(self) -> List[Dict[str, str]]:
        with self.__lock:
            return [msg.data for msg in self.__data]

    __data: List[Message]
    __lock: Lock

    def __init__(self, in_data: List[Message] | Message):

        if isinstance(in_data, Message):
            self.__data = [in_data]
        else:
            self.__data = in_data

        self.__lock = Lock()

    def token_count(self, model: str) -> int:
        with self.__lock:
            return sum(msg.token_count(model) for msg in self.__data)

    def cut_front(self, max_tokens: int, model: str) -> None:
        with self.__lock:
            count: int = self.token_count(model)
            while self.__data:
                count -= self.__data.pop(0).token_count(model)
                if count < max_tokens:
                    break

    def append(self, message: Message) -> None:
        with self.__lock:
            self.__data.append(message)

    def insert(self, message: Message, index: int) -> None:
        with self.__lock:
            self.__data.insert(index, message)

    def pop(self, index: int) -> Message:
        with self.__lock:
            return self.__data.pop(index)

    def copy(self):
        """
        Creates a shallow copy of the conversation - the list of Messages is copied, but the contained messages are
        shared between original and copy. This should be fine since we do not manipulate existing Message objects.

        However, note that the message object CAN be manipulated - the underlying dictionary is accessible since we do
        not want to copy it before using it in the OpenAI request.
        :return: The copied conversation
        """

        with self.__lock:
            return Conversation(copy(self.__data))

    @staticmethod
    def __convert(obj: Any):
        assert isinstance(obj, Conversation) or isinstance(obj, Message) or isinstance(obj, list)
        if isinstance(obj, Conversation):
            return obj
        elif isinstance(obj, list) and all(isinstance(msg, Message) for msg in obj):
            return Conversation(obj)
        elif isinstance(obj, Message):
            return Conversation(obj)
        else:
            raise ValueError(f"Cannot add type '{type(obj)}' to Conversation")

    def __add__(self, other: Any):
        with self.__lock:
            other_conversation: Conversation = Conversation.__convert(other)
            return Conversation(self.__data + other_conversation.__data)

    def __radd__(self, other: Any):
        with self.__lock:
            other_conversation: Conversation = Conversation.__convert(other)
            return Conversation(other_conversation.__data + self.__data)

    def __getitem__(self, item):
        with self.__lock:
            return self.__data[item]
