import abc


class SymEncryptAbc(abc.ABC):

    @abc.abstractmethod
    def encode(self, data: bytes) -> bytes:
        pass

    @abc.abstractmethod
    def decode(self, data: bytes) -> bytes:
        pass
