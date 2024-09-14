# Internal libs
from gpt.tokens import Tokens
from gpt.role import Role
from gpt.langauge import Language

# General utilities
from datetime import datetime
from typing import Dict


class Message:
    """
    A wrapper around the message Dict format used in the OpenAI API with timestamp, language, token count
    """

    __data: Dict[str, str] = None
    __language: Language = None
    __timestamp_start: datetime = None
    __timestamp_end: datetime = None
    __role: Role = None
    __name: str = None
    __content: str = None

    @property
    def data(self) -> Dict[str, str]:
        timestamp: str | None
        if not self.__timestamp_start:
            timestamp = None
        elif self.__timestamp_end:
            timestamp = f"[Start:{self.timestamp_start:%Y-%m-%d %H:%M:%S}, End:{self.timestamp_end:%Y-%m-%d %H:%M:%S}]"
        else:
            timestamp = f"[{self.timestamp_start:%Y-%m-%d %H:%M:%S}]"

        language: str = f"[{self.language.name.lower()}]" if self.language else None

        content: str = f"{timestamp}{language}: {self.content}"

        res: Dict[str, str] = {'role': self.role.name.lower(), 'content': content}
        if self.name:
            res['name'] = self.name
        return res

    @property
    def language(self) -> Language | None:
        return self.__language

    @property
    def timestamp_start(self) -> datetime:
        return self.__timestamp_start

    @property
    def timestamp_end(self) -> datetime:
        return self.__timestamp_end

    @property
    def role(self) -> Role:
        return self.__role

    @property
    def name(self) -> str | None:
        return self.__name

    @property
    def content(self) -> str:
        return self.__content

    def __init__(self,
                 timestamp_start: datetime = None,
                 timestamp_end: datetime = None,
                 role: Role = None,
                 content: str = None,
                 name: str = None,
                 language: Language = Language.EN,
                 raw_dict: Dict[str, str] = None):

        self.__language = language

        self.__timestamp_start = timestamp_start or datetime.now()
        self.__timestamp_end = timestamp_end

        if raw_dict:
            assert not role and not content and not name
            assert 'role' in raw_dict and 'content' in raw_dict
            self.__role = Role[raw_dict['role'].upper()]
            self.__content = raw_dict['content']
            if 'name' in raw_dict:
                self.__name = raw_dict['name']
        else:
            assert not raw_dict
            assert role and content
            self.__role = role
            self.__content = content
            self.__name = name

    def token_count(self, model: str) -> int:
        # See https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb

        tokens_per_message: int = 3
        tokens_per_name: int = 1

        token_count: int = Tokens(self.content, model).count() + tokens_per_message
        if self.name:
            token_count -= tokens_per_name

        return token_count

    def __str__(self):
        return str(self.data)
