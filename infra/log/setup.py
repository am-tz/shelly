# General utilities
from logging.config import dictConfig
from logging import basicConfig, INFO, DEBUG, WARNING, ERROR
from yaml import safe_load
from os.path import join, dirname, pardir, realpath
from typing import Any


class LoggingSetup:
    """Setup logging configuration"""
    DEBUG: int = DEBUG
    INFO: int = INFO
    WARNING: int = WARNING
    ERROR: int = ERROR

    __config: Any = None
    __override_level: int = None
    __default_message_format: str = None
    __default_date_format: str = None

    def __init__(self, override_level: int = None):
        if override_level:
            # noinspection SpellCheckingInspection
            basicConfig(level=override_level,
                        format="[%(asctime)s][(%(threadName)s) %(name)s][%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
        else:
            path = realpath(join(dirname(__file__), pardir, pardir, "files", "other", "logconfig.yaml"))
            with open(path, 'rt') as f:
                config: Any = safe_load(f.read())
            dictConfig(config)
