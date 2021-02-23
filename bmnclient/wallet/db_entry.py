from PySide2.QtCore import QObject


class DbEntry(QObject):
    def __init__(self):
        super().__init__()
        self._rowid = None

    def __get_rowid(self):
        return self._rowid

    def __set_rowid(self, rid):
        assert rid is None or rid > 0
        self._rowid = rid

    def from_args(self, arg_iter: iter):
        raise NotImplementedError()

    def _set_object_name(self, name):
        self.setObjectName(name)

    rowid = property(__get_rowid, __set_rowid)
