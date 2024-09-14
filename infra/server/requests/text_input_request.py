# External libs
from flask_restful import reqparse
from flask_restful.reqparse import RequestParser

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest
from infra.server.requests.utils import parse_enum
from gpt.langauge import Language
from peripherals.text.chat_queues import ChatQueues

# General utils


class TextInputRequest(BaseEndPointRequest):

    __parser: RequestParser = None
    __queues: ChatQueues = None

    def __init__(self, queues: ChatQueues):

        self.__queues = queues

        self.__parser = reqparse.RequestParser()
        self.__parser.add_argument('Message', type=str, required=True)
        self.__parser.add_argument('Language', type=str, required=True)

    def post(self):
        args = self.__parser.parse_args()
        errors = {}
        language = parse_enum(Language, args, errors)
        message = args['Message']

        if errors:
            return errors, 400
        else:
            self.__queues.put_input_message(message, language)
            return ""

    @staticmethod
    def endpoint():
        return "textInput"
