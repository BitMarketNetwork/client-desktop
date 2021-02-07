import QtQuick 2.15
import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("Receive")
    property var coin

    contentItem: BScrollView {
        id: _scrollView
        BControl {
            width: _scrollView.viewWidth
            height: _scrollView.viewHeight
            padding: _applicationStyle.padding

            contentItem: BStackLayout {
                id: _layout
                currentIndex: 0

                BAddressEditBox {
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
                    BDialogSpacer {}
                }

                Loader {
                    active: _layout.currentIndex === 1

                    sourceComponent: BAddressEditBox {
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
                        BDialogSpacer {}
                    }
                }
            }
        }
    }
}
