# External libs
import openai
from openai import OpenAI

# Internal libs
from gpt.conversation import Conversation
from gpt.model import Model
from gpt.role import Role
from gpt.voice import Voice
from gpt.langauge import Language

from peripherals.audio.audio import Audio

from infra.resources_management.manager import Manager
from infra.resources_management.manageable_wrapper import ManageableWrapper

# General utilities
from io import BytesIO
from time import sleep
from os.path import dirname, pardir, realpath, join
from re import match, Match
from typing import Dict


class Client(Manager):

    __client: OpenAI = None

    temperature: float = None
    max_tokens: int = None
    language: Language = None

    __FALLBACK_MODELS: Dict[Model, Model] = {
        Model.GPT__4: Model.GPT__3_5__TURBO,
        Model.GPT__4__1106__PREVIEW: Model.GPT__3_5__TURBO__1106,
        Model.GPT__3_5__TURBO: Model.GPT__4__32K,
    }

    def __init__(self, temperature: float = 1.0, max_tokens: int = None, language: Language = Language.EN):

        super().__init__()

        directory: str = dirname(realpath(__file__))
        key_path = realpath(join(directory, pardir, "files", "other", "key.txt"))

        with open(key_path, "r") as f:
            self.__client = OpenAI(api_key=f.read())
            self.register(ManageableWrapper(like_close=self.__client.close))

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.language = language

    def __handle_rate_limit_error(self, exc: openai.RateLimitError) -> Model:
        pattern: str = r"Rate limit reached for (?P<model>\S+) in organization.+"
        pattern += r"Limit (?P<limit>\d+), Used (?P<usage>\d+), Requested (?P<requested>\d+)\. "
        pattern += r"Please try again in (?P<seconds>\d*\.?\d*)s."

        m: Match = match(pattern, exc.message)

        limit: int = int(m.group('limit'))
        usage: int = int(m.group('usage'))
        requested: int = int(m.group('requested'))
        seconds: float = float(m.group('seconds'))
        model: Model = Model.from_str(m.group('model'))

        message: str = f"Rate limit reached: Requested {requested} tokens, but already used {usage}/{limit}. "

        if seconds < 10:
            sleep(seconds)
            self._logger.warning(message + f"Waiting for {seconds} seconds.")
            return model
        elif model in self.__FALLBACK_MODELS:
            fallback_model: Model = self.__FALLBACK_MODELS[model]
            self._logger.warning(message + f"Falling back to {Model.to_literal(fallback_model)}.")
            return fallback_model
        else:
            raise exc

    def query_chat(self, conversation: Conversation,
                   model: Model = Model.GPT__4,
                   json_format: bool = False,
                   temperature: float | None = None) -> str:

        try:
            if json_format:
                assert model == Model.GPT__4__1106__PREVIEW

            response = self.__client.chat.completions.create(
                model=Model.to_literal(model),
                messages=conversation.data,
                temperature=temperature or self.temperature,
                max_tokens=self.max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "json_object"} if json_format else {"type": "text"}
            )
            return response.choices[0].message.content.strip()
        except openai.RateLimitError as err:
            fallback_model: Model = self.__handle_rate_limit_error(err)
            return self.query_chat(conversation, fallback_model, json_format, temperature)
        except openai.BadRequestError as err:
            if model in self.__FALLBACK_MODELS:
                return self.query_chat(conversation, self.__FALLBACK_MODELS[model], json_format, temperature)
            else:
                raise err

    def query_whisper(self, audio: Audio) -> str:

        # Workaround because openai API reads the file type from the file handle name...
        stream: BytesIO = audio.stream()
        stream.name = "dummy.wav"

        try:
            response = self.__client.audio.transcriptions.create(
                model=Model.to_literal(Model.WHISPER__1),
                file=stream,
                temperature=self.temperature,
                language=self.language.name.lower(),
                response_format="text"
                )
            return str(response)
        except openai.RateLimitError as err:
            self.__handle_rate_limit_error(err)
            return self.query_whisper(audio)

    def query_tts(self, input_text: str, voice: Voice = Voice.ECHO):

        try:
            response = self.__client.audio.speech.create(
                model=Model.to_literal(Model.TTS__1),
                input=input_text,
                voice=Voice.to_literal(voice),
                response_format="opus",
                speed=1.0
            )

            buffer: BytesIO = BytesIO()
            for chunk in response.iter_bytes(chunk_size=4096):
                buffer.write(chunk)
            buffer.seek(0)

            return Audio(ogg_buffer=buffer)
        except openai.RateLimitError as err:
            self.__handle_rate_limit_error(err)
            return self.query_tts(input_text, voice)

    def close(self) -> None:
        self.__client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    from infra.log.setup import LoggingSetup
    LoggingSetup(override_level=LoggingSetup.DEBUG)

    from gpt.message import Message
    from peripherals.audio.input import Input
    from peripherals.audio.output import Output

    with Client(language=Language.EN) as socket:
        with Input() as inp:
            record: Audio
            _, record = inp.queue.get()
            transcription = socket.query_whisper(record)
            print(f"Whisper understood: {transcription}")
            transcribed_message = Message(role=Role.USER, content=transcription)
            res = socket.query_chat(Conversation(transcribed_message))
            print(f"GPT answers: {res}")
            speech = socket.query_tts(res)
            with Output() as output:
                output.play(speech)
