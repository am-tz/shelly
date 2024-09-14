# Internal libs
from infra.resources_management.manageable import Manageable

# General utilities
from abc import abstractmethod
from threading import Thread
from typing import List, TypeVar


class Manager(Manageable):
    """
    A registry for ThreadedApp objects, to manage starting/stopping them.
    Can also have sub-managers
    Note: The manager itself is NOT thread-safe.
    """

    __managed_objects: List[Manageable] = None
    __T: TypeVar = TypeVar("__T", bound=Manageable)

    @abstractmethod
    def __init__(self):
        super().__init__()
        self.__managed_objects = []

    def register(self, obj: __T) -> __T:
        """
        Registers a manageable object to be managed by self
        :param obj: object inheriting from Manageable
        :return: None
        """
        if obj in self.__managed_objects:
            self._logger.error(f"{obj} is already registered")
            raise RuntimeError

        if isinstance(obj, Manager) and (self is obj or self in obj):
            self._logger.exception(f"Registering {obj} in {self} would result in a loop")
            raise RuntimeError

        self.__managed_objects.append(obj)
        return obj

    def start(self):
        for obj in self.__managed_objects:
            obj.start()

    def close(self):
        self.clean_up()
        super().close()
        if self.__managed_objects:
            closer_threads: List[Thread] = [Thread(target=obj.close) for obj in self.__managed_objects]

            for thread in closer_threads:
                thread.start()

            for thread in closer_threads:
                thread.join()

    def clean_up(self):
        self.__managed_objects = [t for t in self.__managed_objects if not t.was_closed]

    def __contains__(self, item) -> bool:
        """
        Recursive check if the manageable item is contained in this manager or any of its sub-managers.
        :param item: A ThreadedApp or an AppManager
        :return: True if the item is found, else False
        """
        return item in self.__managed_objects or any(item in obj for obj in self.__managed_objects)
