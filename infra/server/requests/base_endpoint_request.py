# External libs
from flask_restful import Resource

# General utilities
from abc import ABC, abstractmethod


class BaseEndPointRequest(Resource, ABC):

    @staticmethod
    @abstractmethod
    def endpoint() -> str:
        pass
