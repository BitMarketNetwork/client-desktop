import logging

import PySide2.QtCore as qt_core

from client import meta

log = logging.getLogger(__name__)


class DbEntry(meta.QSeq):

    def __init__(self, parent):
        super().__init__(parent=parent)
        self._rowid = None

    def __get_rowid(self):
        return self._rowid

    def __set_rowid(self, rid):
        assert rid is None or rid > 0
        self._rowid = rid

    def from_args(self, arg_iter: iter):
        raise NotImplementedError()

    def _set_object_name(self, name):
        super().setObjectName(name)

    rowid = property(__get_rowid, __set_rowid)
