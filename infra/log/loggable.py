# General utilities
from abc import ABC, abstractmethod
from logging import Logger, getLogger


class Loggable(ABC):

    @property
    def _logger(self) -> Logger:
        return self.__logger

    __logger: Logger = None

    @abstractmethod
    def __init__(self):
        self.__logger = getLogger(self.__module__)
