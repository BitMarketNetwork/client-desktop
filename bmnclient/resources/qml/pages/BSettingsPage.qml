import "../application"
import "../basiccontrols"

BApplicationPage {
    id: _base

    title: qsTr("Application settings")

    list.currentIndex: 0
    stack.currentIndex: 1

    BSettingsGeneralPane {}

    BSettingsCoinsPane {}

    BSettingsAdvancedPane {
        onBackupWallet: {
        }
        onRestoreWallet: {
        }
        onClearWallet: {
        }

        onRevealSeedPhraseWallet: {
            _applicationManager.openRevealSeedPharseDialog()
        }
    }
}
