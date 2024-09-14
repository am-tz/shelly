# External libs
from socket import gethostname, gethostbyname

HOST: str = gethostbyname(gethostname())
PORT: int = 65000
