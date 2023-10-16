import QtQuick
import QtQuick.Dialogs

FileDialog {
    id: _base

    enum Type {
        Export,
        Import
    }

    property int type: BBackupFileDialog.Type.Export

    fileMode: _base.type === BBackupFileDialog.Type.Export ? FileDialog.SaveFile : FileDialog.OpenFile
    nameFilters: ["JSON (*.json)"]
    title: {
        switch (type) {
        case BBackupFileDialog.Type.Export:
            return qsTr("Select a directory for save")
        case BBackupFileDialog.Type.Import:
            return qsTr("Select backup file for import")
        }
    }
}
