# External libs

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest

# General utils
from subprocess import call


class ShutdownRequest(BaseEndPointRequest):

    def get(self):
        call("sudo shutdown --poweroff")

    @staticmethod
    def endpoint():
        return "shutdown"
