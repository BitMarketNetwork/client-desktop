import "../application"
import "../basiccontrols"
import "../dialogs"

BApplicationPage {
    id: _base

    title: qsTr("Application settings")

    list.currentIndex: 0
    stack.currentIndex: 1

    BSettingsGeneralPane {}

    BSettingsCoinsPane {}

    BSettingsAdvancedPane {
        BBackupFileDialog {
            id: _fileDialog

            onAccepted: {
                BBackend.keyStore.onExportBackupWallet(_fileDialog.currentFile)
            }
        }
        onBackupWallet: {
            _fileDialog.open()
        }
        onRestoreWallet: {
        }
        onClearWallet: {
        }
    }
}
