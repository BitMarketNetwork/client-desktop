import enum
from typing import Iterable, Any
import json
import logging
log = logging.getLogger(__name__)

FILE_HEADER = b'\xff\xeb\xbe'


class SerializeMixin:

    def to_table(self) -> dict:
        raise NotImplementedError()

    def from_table(self, table: dict):
        raise NotImplementedError()


class SerializationType(enum.IntFlag):
    DEBUG = enum.auto()
    CYPHER = enum.auto()


class SerializationError(Exception):
    pass


class Serializator:

    def __init__(self, type_: SerializationType = SerializationType.DEBUG, password: str = None):
        self._type = type_
        if SerializationType.DEBUG not in self._type:
            raise NotImplementedError(
                "Only debug serialization supported for a while")
        self._main_table = {
            "meta": {
                "type": self._type,
            }
        }
        self._password = password

    def add_many(self, name: str, what: Iterable[SerializeMixin]):
        self._main_table[name] = [s.to_table() for s in what]

    def add_one(self, name: str, what: Any):
        log.debug(f"field to ser => {name}: {what}")
        if what is None:
            log.warning(f"Attempt to serialize null field: {name}")
        elif isinstance(what, SerializeMixin):
            self._main_table[name] = what.to_table()
        else:
            self._main_table[name] = what

    def to_file(self, fpath: str, pretty: bool = False):
        kwargs = {}
        if pretty:
            kwargs.update({
                "indent":   4,
                "separators":   (',', ': '),
            })
        try:
            if SerializationType.CYPHER in self._type:
                with open(fpath, "wb") as fh:
                    txt = json.dumps(self._main_table, **kwargs)
                    #fh.write(FILE_HEADER)
                    #fh.write(self._type.to_bytes(length=1, byteorder="little"))
                    #fh.write(aes.encode(txt, True))
            else:
                with open(fpath, "w") as fh:
                    json.dump(self._main_table, fh, **kwargs)
        except OSError as oe:
            raise SerializationError(f"Can't save to {fpath}") from oe
