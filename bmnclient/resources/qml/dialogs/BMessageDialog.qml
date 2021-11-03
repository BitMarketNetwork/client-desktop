import QtQuick 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    property int type: BMessageDialog.Type.Information
    property alias text: _message.text

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

                Keys.onReturnPressed: {
                    Qt.callLater(accept)
                }

            }
            onLoaded: {
                _buttonBox.addItem(item)
                item.forceActiveFocus(Qt.TabFocus)
            }
        }

        Loader {
            active: _base.type === BMessageDialog.Type.AskYesNo
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                parent: _buttonBox
                text: BCommon.button.yesRole

                Keys.onReturnPressed: {
                    Qt.callLater(accept)
                }

            }
            onLoaded: {
                _buttonBox.addItem(item)
                item.forceActiveFocus(Qt.TabFocus)
            }
        }
        Loader {
            active: _base.type === BMessageDialog.Type.AskYesNo
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
                parent: _buttonBox
                text: BCommon.button.noRole

                Keys.onReturnPressed: {
                    Qt.callLater(reject)
                }
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
    }
}
