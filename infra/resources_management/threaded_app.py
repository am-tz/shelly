from infra.resources_management.manageable import Manageable

# General utilities
from abc import abstractmethod
from threading import Thread, Lock
from copy import copy
from time import sleep
from typing import List, Callable


class ThreadedApp(Manageable):
    """
    A base class for an application running one or several threads with the same lifetime as the application itself.
    """

    __threads: List[Thread] = None
    __threads_lock: Lock = None

    thread_startup_delay: float = 1.0

    @abstractmethod
    def __init__(self):
        super().__init__()
        self.__threads = []
        self.__threads_lock = Lock()

    def start(self) -> None:
        """
        Starts all threads
        :return: None
        """
        for thread in self.__thread_safe_threads():
            thread.start()
            self._logger.debug(f"{thread.name} started - waiting for {self.thread_startup_delay}s..")
            sleep(self.thread_startup_delay)
            self._logger.debug(f"Leaving constructor for {thread.name}")

    def close(self) -> None:
        """
        Closes all threads
        :return: None
        """
        super().close()
        for thread in self.__thread_safe_threads():
            thread.join()
            self._logger.debug(f"{thread.name} closed")

    def _make_thread(self, target: Callable) -> None:
        """
        If the ThreadedApp needs a thread to run during its whole lifetime, the app should use this method to create it
        :param target: The callable target of the thread
        :return: None
        """
        with self.__threads_lock:
            target_name: str = target.__name__
            if target_name.startswith("__"):
                target_name = target_name[2:]
            self.__threads.append(Thread(target=target, name=f"Thread '{target_name}'"))

    def __thread_safe_threads(self) -> List[Thread]:
        with self.__threads_lock:
            return copy(self.__threads)

    def __contains__(self, item):
        return item in self.__thread_safe_threads()
