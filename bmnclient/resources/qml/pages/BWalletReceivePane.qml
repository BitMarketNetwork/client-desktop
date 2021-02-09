import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("Receive")
    property var coin

    contentItem: BStackLayout {
        id: _layout
        currentIndex: 0

        BDialogScrollableLayout {
            contentLayoutItem: BAddressEditBox {
                id: _inputBox
                coin: _base.coin
                type: BAddressEditBox.Type.GenerateRecipient

                BDialogInputButtonBox {
                    BButton {
                        BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                        text: _inputBox.acceptText
                    }
                    BButton {
                        BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                        text: BStandardText.button.resetRole
                    }
                    onReset: {
                        _inputBox.reset()
                    }
                    onAccepted: {
                        BBackend.receiveManager.accept(_inputBox.useSegwit, _inputBox.labelText, _inputBox.commentText)
                        _layout.currentIndex = 1
                    }
                }
            }
        }

        Loader {
            active: _layout.currentIndex === 1

            sourceComponent: BDialogScrollableLayout {
                contentLayoutItem: BAddressEditBox {
                    id: _resultBox
                    coin: _base.coin
                    type: BAddressEditBox.Type.ViewRecipient

                    // TODO bad
                    addressText: BBackend.receiveManager.address
                    labelText: BBackend.receiveManager.label
                    commentText: BBackend.receiveManager.message
                    useSegwit: _inputBox.useSegwit // TODO

                    BDialogInputButtonBox {
                        BButton {
                            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                            text: _resultBox.acceptText
                        }
                        BButton {
                            BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                            text: BStandardText.button.resetRole
                        }
                        onReset: {
                            _layout.currentIndex = 0
                        }
                        onAccepted: {
                            BBackend.uiManager.copyToClipboard(_resultBox.addressText)
                        }
                    }
                }
            }
        }
    }
}
