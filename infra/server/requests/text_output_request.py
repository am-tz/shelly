# External libs

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest
from peripherals.text.chat_queues import ChatQueues

# General utils
from typing import List


class TextOutputRequest(BaseEndPointRequest):

    __queues: ChatQueues = None

    def __init__(self, queues: ChatQueues):

        self.__queues = queues

    def get(self):

        output: List[str] = []
        while not self.__queues.output_queue.empty():
            output.append(str(self.__queues.output_queue.get(True, 0.1)))

        return "\n".join(output)

    @staticmethod
    def endpoint():
        return "textOutput"
