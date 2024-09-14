# External libs
from flask_restful import Api

# Internal libs
from infra.server.requests.base_endpoint_request import BaseEndPointRequest

# General utilities
from typing import Dict, Any, Type


def parse_enum(enum_class: Any, args: Any, errors: Dict[str, Any]) -> Any:
    value_string = args[enum_class.__name__]
    if value_string in [x.name for x in enum_class]:
        return enum_class[value_string]
    else:
        errors[enum_class.__name__] = f"Invalid value '{value_string}'"
        return None


def pack_enums(*enums: Any) -> Dict[str, str]:
    return {enum.__class__.__name__: enum.name for enum in enums}


def add_resource(api: Api, request: Type[BaseEndPointRequest], **kwargs) -> None:
    api.add_resource(request, f'/{request.endpoint()}', resource_class_kwargs=kwargs)
