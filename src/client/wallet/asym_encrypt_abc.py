
import abc


class AsymEncryptAbc(abc.ABC):

    @abc.abstractproperty
    def password(self) -> str:
        pass

    @abc.abstractmethod
    def encode(self, data: bytes) -> bytes:
        pass

    @abc.abstractmethod
    def decode(self, data: bytes) -> bytes:
        pass