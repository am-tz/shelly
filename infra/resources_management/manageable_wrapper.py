# Internal libs
from infra.resources_management.manageable import Manageable

# General utilities
from typing import Callable


class ManageableWrapper(Manageable):
    """
    Wraps a resource that conceptually fits the start/close interface of Manageable, but uses different words,
    in a manageable format.
    """

    __start_imp: Callable = None
    __close_imp: Callable = None
    
    def __init__(self, like_start: Callable = None, like_close: Callable = None):
        super().__init__()
        self.__start_imp = like_start
        self.__close_imp = like_close

    def start(self):
        if self.__start_imp:
            self.__start_imp()

    def close(self):
        super().close()
        if self.__close_imp:
            self.__close_imp()

    def __contains__(self, item) -> bool:
        """
        This wrapper does nto do any containment checks. This just exists to fit the manageable interface
        :param item: Irrelevant
        :return: Always returns False
        """
        return False
