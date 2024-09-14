from paramiko import MissingHostKeyPolicy


class AllowAllKeys(MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return
