from dataclasses import dataclass


@dataclass
class Server:
    name: str
    url: str
    premium: bool