from abc import ABC, abstractmethod


class BaseResolver(ABC):

    @abstractmethod
    def resolve(self, url: str) -> str:
        """
        Devuelve la URL final del video (.mp4 o .m3u8)
        """
        raise NotImplementedError