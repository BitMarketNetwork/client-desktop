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
        applicationFont: Qt.font(BBackend.settingsManager.font)
        onApplicationFontChanged: {
            BBackend.settingsManager.font = {
                "family": applicationFont.family,
                "pointSize": applicationFont.pointSize,
            }
        }

        useChangeAddress: BBackend.settingsManager.newAddressFroLeftover
        onUseChangeAddressChanged: {
            BBackend.settingsManager.newAddressFroLeftover = useChangeAddress
        }

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
