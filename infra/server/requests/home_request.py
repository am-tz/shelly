# External libs
from flask import Response, render_template

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest


class HomeRequest(BaseEndPointRequest):

    def get(self):
        return Response(response=render_template('index.html'))

    @staticmethod
    def endpoint():
        return ""
