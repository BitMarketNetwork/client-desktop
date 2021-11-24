import QtQuick
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

    onAboutToShow: {
        try {
            for (let i = 0; i < footer.contentChildren.length; ++i) {
                let item = footer.contentChildren[i]
                if (item.BDialogButtonBox.buttonRole === BDialogButtonBox.AcceptRole) {
                    if (item.enabled) {
                        item.forceActiveFocus(Qt.TabFocus)
                    }
                    break
                }
            }
        } catch (e) {}
    }
}
