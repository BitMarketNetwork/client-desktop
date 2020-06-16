
import logging
import pathlib

import PySide2.QtWidgets as qt_widgets
import PySide2.QtGui as qt_qui
log = logging.getLogger(__name__)

BACKUP_EXTENSION = ".bmn"


class ImportExportDialog:
    _init_dir = ""

    def __init__(self, *args, **kwargs):
        pass

    def doImport(self, caption: str, ext: str = BACKUP_EXTENSION) -> str:
        filepath, _ = qt_widgets.QFileDialog.getOpenFileName(
            None,
            caption=caption,
            dir=self._init_dir,
            filter=f"Wallet files (*{ext});;All files (*)",
            options= qt_widgets.QFileDialog.Option.DontUseNativeDialog,
        )
        self._update(filepath)
        return filepath

    def doExport(self, caption: str, ext: str = BACKUP_EXTENSION) -> str:
        filepath, ftr = qt_widgets.QFileDialog.getSaveFileName(
            None,
            caption=caption,
            dir=self._init_dir,
            filter=f"Wallet files (*{ext});;All files (*)",
            options= qt_widgets.QFileDialog.Option.DontUseNativeDialog,
        )
        log.debug(f"export current filter: {ftr}")
        if ext in ftr and not filepath.endswith(ext):
            filepath += ext
        self._update(filepath)
        return filepath
    
    def _update(self, filepath: str):
        if filepath:
            self._init_dir = pathlib.Path(filepath).parent
            log.debug(f"init dir:{self._init_dir}")
