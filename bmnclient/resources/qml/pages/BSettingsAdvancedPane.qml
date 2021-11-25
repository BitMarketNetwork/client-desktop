import QtQuick.Dialogs
import "../application"
import "../basiccontrols"
import "../dialogs"

BPane {
    id: _base
    property string title: qsTr("Advanced")
    property string iconPath: _applicationManager.imagePath("icon-tools.svg")

    signal backupWallet
    signal restoreWallet
    signal clearWallet

    contentItem: BDialogScrollableLayout {
        BDialogPromptLabel {
            text: qsTr("Application font:")
        }
        BDialogInputButton {
            id: _fontDialogButton
            text: qsTr("%1, %2")
                    .arg(_fontDialog.currentFont.family)
                    .arg(Math.round(_fontDialog.currentFont.pointSize))
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
            stateModel: BBackend.settings.fiatRateService
        }

        BDialogPromptLabel {
            text: qsTr("Fiat currency:")
        }
        BDialogInputComboBox {
            stateModel: BBackend.settings.fiatCurrency
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
            text: qsTr("Reveal Seed Phrase...")
            onClicked: {
                BBackend.keyStore.onRevealSeedPhrase()
            }
        }
    }

    BMessageDialog {
        id: _resetMessageBox
        text: qsTr(
                "This will destroy all your keys and lead to a risk of losing money!"
                  + " Please make sure that you made a backup."
                  + "\n\nContinue?")
        type: BMessageDialog.Type.AskYesNo
    }

    FontDialog {
        id: _fontDialog
        modality: Qt.WindowModal
        title: qsTr("Select a preferable font")
        selectedFont: Qt.font(BBackend.settings.font.current)
        onSelectedFontChanged: {
            BBackend.settings.font.current = {
                "family": selectedFont.family,
                "pointSize": selectedFont.pointSize,
            }
        }
    }
}
