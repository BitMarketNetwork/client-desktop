import QtQuick.Dialogs 1.3
import "../application"
import "../basiccontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Advanced")
    property string iconPath: _applicationManager.imagePath("icon-tools.svg")

    property alias useChangeAddress: _useChangeAddress.checked

    signal backupWallet
    signal restoreWallet
    signal clearWallet
    signal revealSeedPhraseWallet

    contentItem: BDialogScrollableLayout {
        BDialogPromptLabel {
            text: qsTr("Application font:")
        }
        BDialogInputButton {
            id: _fontDialogButton
            text: qsTr("%1, %2")
                    .arg(_fontDialog.font.family)
                    .arg(Math.round(_fontDialog.font.pointSize))
            onClicked: {
                _fontDialog.open()
            }
        }

        BDialogPromptLabel {
            text: qsTr("Hide to tray on closing:")
        }
        BDialogInputSwitch {
            checked: BBackend.settings.systemTray.closeToTray
            onCheckedChanged: {
                BBackend.settings.systemTray.closeToTray = checked
            }
        }

        BDialogSeparator {}

        BDialogPromptLabel {
            text: qsTr("Fiat rate service:")
        }
        BDialogInputComboBox {
            model: BBackend.settingsManager.fiatRateServiceList
            currentIndex: BBackend.settingsManager.currentFiatRateServiceIndex
            onCurrentIndexChanged: {
                BBackend.settingsManager.currentFiatRateServiceIndex = currentIndex
            }
        }

        BDialogPromptLabel {
            text: qsTr("Fiat currency:")
        }
        BDialogInputComboBox {
            model: BBackend.settingsManager.fiatCurrencyList
            currentIndex: BBackend.settingsManager.currentFiatCurrencyIndex
            onCurrentIndexChanged: {
                BBackend.settingsManager.currentFiatCurrencyIndex = currentIndex
            }
        }

        BDialogSeparator {}

        BDialogPromptLabel {

            text: qsTr("Always send change to a new address:")
        }
        BDialogInputSwitch {
            id: _useChangeAddress
        }

        BDialogSeparator {}

        BDialogInputButton {
            BLayout.columnSpan: parent.columns
            BLayout.alignment:
                (_applicationStyle.dialogInputAlignment & ~Qt.AlignHorizontal_Mask)
                | Qt.AlignHCenter
            text: qsTr("Backup wallet...")
            enabled: false
            onClicked: {
                _base.backupWallet()
            }
        }
        BDialogInputButton {
            BLayout.columnSpan: parent.columns
            BLayout.alignment:
                (_applicationStyle.dialogInputAlignment & ~Qt.AlignHorizontal_Mask)
                | Qt.AlignHCenter
            text: qsTr("Restore wallet...")
            enabled: false
            onClicked: {
                _resetMessageBox.title = text
                _resetMessageBox.accepted.connect(_base.restoreWallet)
                _resetMessageBox.open()
            }
        }
        BDialogInputButton {
            BLayout.columnSpan: parent.columns
            BLayout.alignment:
                (_applicationStyle.dialogInputAlignment & ~Qt.AlignHorizontal_Mask)
                | Qt.AlignHCenter
            text: qsTr("Clear wallet...")
            enabled: false
            onClicked: {
                _resetMessageBox.title = text
                _resetMessageBox.accepted.connect(_base.clearWallet)
                _resetMessageBox.open()
            }
        }

        BDialogSeparator {}

        BDialogInputButton {
            BLayout.columnSpan: parent.columns
            BLayout.alignment:
                (_applicationStyle.dialogInputAlignment & ~Qt.AlignHorizontal_Mask)
                | Qt.AlignHCenter
            text: qsTr("Reveal seed phrase...")
            onClicked: {
                _base.revealSeedPhraseWallet()
            }
        }
    }

    BMessageDialog {
        id: _resetMessageBox
        text: qsTr(
                "This will destroy all your keys and lead to a risk of losing money!"
                  + " Please make sure that you made a backup."
                  + "\n\nContinue?")
        standardButtons: BMessageDialog.Yes | BMessageDialog.No
    }

    FontDialog {
        id: _fontDialog
        modality: Qt.WindowModal
        title: qsTr("Select a preferable font")
        font: Qt.font(BBackend.settings.font.current)
        onFontChanged: {
            BBackend.settings.font.current = {
                "family": font.family,
                "pointSize": font.pointSize,
            }
        }
    }
}
