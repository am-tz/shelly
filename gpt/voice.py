# General utilities
from enum import Enum, auto
from typing import Literal, Any


class Voice(Enum):

    ALLOY = auto()
    ECHO = auto()
    FABLE = auto()
    ONYX = auto()
    NOVA = auto()
    SHIMMER = auto()

    @staticmethod
    def to_literal(voice: Any) -> Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]:
        return voice.name.lower()
