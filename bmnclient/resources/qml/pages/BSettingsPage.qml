import "../application"
import "../basiccontrols"

BApplicationPage {
    id: _base

    title: qsTr("Application settings")

    list.currentIndex: 0
    stack.currentIndex: 1

    BSettingsGeneralPane {
        fiatUnityModel: BBackend.settingsManager.currencyModel
        currentFiatUnitIndex: BBackend.settingsManager.currencyIndex
        onCurrentFiatUnitIndexChanged: {
            BBackend.settingsManager.currencyIndex = currentFiatUnitIndex
        }
    }

    BSettingsCoinsPane {
        coinListModel: BBackend.coinManager.staticCoinModel
    }

    BSettingsAdvancedPane {
        applicationFont: Qt.font(BBackend.settingsManager.font)
        onApplicationFontChanged: {
            BBackend.settingsManager.font = {
                "family": applicationFont.family,
                "pointSize": applicationFont.pointSize,
            }
        }

        fiatValueSourceModel: BBackend.settingsManager.rateSourceModel
        currentFiatValueSourceIndex: BBackend.settingsManager.rateSourceIndex
        onCurrentFiatValueSourceIndexChanged: {
            BBackend.settingsManager.rateSourceIndex = currentFiatValueSourceIndex
        }

        useChangeAddress: BBackend.settingsManager.newAddressFroLeftover
        onUseChangeAddressChanged: {
            BBackend.settingsManager.newAddressFroLeftover = useChangeAddress
        }

        onBackupWallet: {
            BBackend.keyStore.exportWallet()
        }
        onRestoreWallet: {
            BBackend.keyStore.importWallet()
        }
        onClearWallet: {
            BBackend.keyStore.resetWallet()
        }

        onRevealSeedPhraseWallet: {
            _applicationManager.openRevealSeedPharseDialog()
        }
    }
}
