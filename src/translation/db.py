import plyvel
from typing import Optional
import pathlib


def folder(lang: str) -> str:
    db_path = pathlib.Path(__file__).parent / "db"
    if not db_path.exists():
        db_path.mkdir()
    return str(db_path / lang)


class Db:

    def __init__(self, lang: str):
        self._ptr = plyvel.DB(folder(lang),
                              create_if_missing=True
                              )

    def close(self):
        if not self._ptr.closed:
            self._ptr.close()

    def add(self, key: str, value: str):
        self._ptr.put(
            key.encode(),
            value.encode(),
        )

    def get(self, key:str) -> Optional[str]:
        res = self._ptr.get( key.encode() )
        return res.decode() if res else None