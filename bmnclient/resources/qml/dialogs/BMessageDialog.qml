import QtQuick 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base

    property alias text: _message.text
    property int type: BMessageDialog.Type.Information

    enum Type {
        Information,
        AskYesNo
    }

    title: Qt.application.name
    contentItem: BDialogLayout {
        columns: 1
        BDialogDescription {
            id: _message
        }
    }

    footer: BDialogButtonBox {
        id: _buttonBox

        Loader {
            active: _base.type === BMessageDialog.Type.Information
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                parent: _buttonBox
                text: BCommon.button.okRole
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }

        Loader {
            active: _base.type === BMessageDialog.Type.AskYesNo
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                parent: _buttonBox
                text: BCommon.button.yesRole
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
        Loader {
            active: _base.type === BMessageDialog.Type.AskYesNo
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
                parent: _buttonBox
                text: BCommon.button.noRole
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
    }
}
