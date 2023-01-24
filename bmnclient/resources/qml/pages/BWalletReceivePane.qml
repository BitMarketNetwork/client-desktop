import QtQuick
import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("Receive")
    property var coin // CoinModel

    contentItem: BStackLayout {
        id: _layout
        currentIndex: 0

        BDialogScrollableLayout {
            contentLayoutItem: BAddressEditBox {
                id: _inputBox
                coin: _base.coin
                type: BAddressEditBox.Type.CreateRecipient

                BDialogInputButtonBox {
                    BButton {
                        BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                        text: _inputBox.acceptText
                    }
                    BButton {
                        BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                        text: BCommon.button.clearRole
                    }
                    onReset: {
                        _base.coin.receiveManager.clear()
                        _inputBox.clear()
                    }
                    onAccepted: {
                        if (_base.coin.receiveManager.create(
                                    _inputBox.isSegwit,
                                    _inputBox.labelText,
                                    _inputBox.commentText)) {
                            _layout.currentIndex = 1
                        } else {
                            // TODO show error
                        }
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

                    addressNameText: _base.coin.receiveManager.name
                    labelText: _base.coin.receiveManager.label
                    commentText: _base.coin.receiveManager.comment
                    isSegwit: _base.coin.receiveManager.isSegwit

                    BDialogInputButtonBox {
                        BButton {
                            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                            text: _resultBox.acceptText
                        }
                        BButton {
                            BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                            text: qsTr("Create again")
                        }
                        onReset: {
                            _layout.currentIndex = 0
                            _inputBox.clear()
                        }
                        onAccepted: {
                            BBackend.clipboard.text = _resultBox.addressNameText
                        }
                    }
                }
            }
        }
    }
}
