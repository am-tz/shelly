# General utilities
from infra.log.loggable import Loggable
from abc import abstractmethod
from threading import Event


class Manageable(Loggable):

    _was_closed: Event

    @property
    def was_closed(self):
        return self._was_closed.is_set()

    @abstractmethod
    def __init__(self):
        super().__init__()
        self._was_closed = Event()

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        self._was_closed.set()

    @abstractmethod
    def __contains__(self, item):
        pass

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
