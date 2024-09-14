from enum import Enum, auto
from typing import Any, Literal


class Model(Enum):

    # Chat models
    TEXT__CURIE__001 = auto()
    GPT__3_5__TURBO = auto()
    GPT__4 = auto()
    GPT__4__32K = auto()

    # JSON-capable models
    GPT__4__1106__PREVIEW = auto()
    GPT__3_5__TURBO__1106 = auto()

    # Transcription models
    WHISPER__1 = auto()

    # Text to speech models
    TTS__1 = auto()

    # Tokenizer models
    CL100K__BASE = auto()

    @staticmethod
    def to_literal(model: Any) -> Literal["text-curie-001",
                                          "gpt-3.5-turbo",
                                          "gpt-4",
                                          "gpt-4-32k",
                                          "gpt-4-1106-preview",
                                          "gpt-3.5-turbo-1106",
                                          "whisper-1",
                                          "tts-1",
                                          "cl100k-base"]:
        name = model.name
        name = name.replace("__", "-")
        name = name.replace("_", ".")
        return name.lower()

    @staticmethod
    def from_str(name: str) -> Any:
        name = name.replace("-", "__")
        name = name.replace(".", "_")
        return Model[name.upper()]
