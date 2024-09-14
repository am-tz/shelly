# External libs
from flask_restful import reqparse
from flask_restful.reqparse import RequestParser

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest
from peripherals.wheels.move import Direction, Speed, Move
from infra.server.requests.utils import parse_enum


class MoveRequest(BaseEndPointRequest):

    __move: Move = None
    __parser: RequestParser = None

    def __init__(self, move_implementation: Move):

        self.__move = move_implementation

        self.__parser = reqparse.RequestParser()
        self.__parser.add_argument('Direction', type=str, required=True)
        self.__parser.add_argument('Speed', type=str, required=True)

    def post(self):
        args = self.__parser.parse_args()
        errors = {}
        direction = parse_enum(Direction, args, errors)
        speed = parse_enum(Speed, args, errors)

        if errors:
            return errors, 400
        else:
            return self.__move.start_move(direction, speed)

    @staticmethod
    def endpoint() -> str:
        return "move"
