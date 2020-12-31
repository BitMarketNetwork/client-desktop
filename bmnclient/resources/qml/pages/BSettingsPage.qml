import "../application"
import "../basiccontrols"

BApplicationPage {
    id: _base
    signal restartApplication

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
        applicationFont: _applicationWindow.font
        onApplicationFontChanged: {
            _applicationWindow.font = applicationFont
            BBackend.settingsManager.fontData = { // TODO
                "family": applicationFont.family,
                "pointSize": applicationFont.pointSize,
                "bold": applicationFont.bold
            }
            restartApplication()
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
