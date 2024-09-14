# External libs
from paramiko import SSHClient

# Internal libs
from infra.deployment.allow_all_keys import AllowAllKeys
from infra.log.loggable import Loggable

# General utilities
from os.path import expanduser
from time import sleep
from typing import List


class Shell(Loggable):

    host: str = None
    user: str = None
    __password: str = None

    client: SSHClient = None

    def __init__(self, host: str, password: str, user: str):
        super().__init__()
        self.host = host
        self.user = user
        self.__password = password

        self.client = SSHClient()
        self.client.load_system_host_keys()
        self.client.load_host_keys(expanduser('~/.ssh/known_hosts'))
        self.client.set_missing_host_key_policy(AllowAllKeys())

    def execute(self, commands: List[str]) -> None:
        self.client.connect(self.host, username=self.user, password=self.__password)

        channel = self.client.invoke_shell()
        with channel.makefile('wb') as stdin:
            with channel.makefile('rb') as stdout:
                self._logger.info("Sending commands")
                stdin.write("\n".join(commands))
                self._logger.info("Waiting for 10 seconds")
                sleep(10.0)
                self._logger.info("Reading Output:")
                self._logger.info("-"*80)
                while True:
                    output_log: str = stdout.readline().decode('utf-8')
                    self._logger.info(output_log)

                    if stdout.channel.exit_status_ready():
                        break
                self._logger.info("-"*80)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
