# External libs
from tiktoken import Encoding, get_encoding, encoding_for_model

# Internal libs
from gpt.model import Model

from infra.log.loggable import Loggable

# General utilities
from typing import List


class Tokens(Loggable):
    
    enc: Encoding = None
    text: str
    tokens: List[int]

    def __init__(self, text: str, model: str) -> None:

        super().__init__()

        try:
            self.enc = encoding_for_model(model)
        except KeyError:
            self._logger.warning(f"Encoding model for '{model}' not found. Using '{Model.CL100K__BASE}' encoding.")
            self.enc = get_encoding(Model.to_literal(Model.CL100K__BASE))

        self.text = text
        self.tokens = self.enc.encode(text)

    def count(self) -> int:
        return len(self.tokens)

    def words(self, start: int = 0, end: int = 0) -> str:
        if end == 0:
            end = self.count()
        return self.enc.decode(self.tokens[start:end])
