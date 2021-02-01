import "../application"
import "../basiccontrols"
import "../coincontrols"

// TODO show result in BAddressEditBox.Type.*View
BDialog {
    property alias coin: _box.coin
    property alias type: _box.type

    property alias addressText: _box.addressText
    property alias labelText: _box.labelText
    property alias commentText: _box.commentText
    property alias useSegwit: _box.useSegwit

    title: _box.dialogTitleText
    contentItem: BAddressEditBox {
        id: _box
        onAddressTextChanged: {
            if (type === BAddressEditBox.Type.AddWatchOnly) {
                // TODO show invalid address message
                _acceptButton.enabled = BBackend.coinManager.isValidAddress(
                            coin.shortName,
                            addressText)
            }
        }
    }
    footer: BDialogButtonBox {
        BButton {
            id: _acceptButton
            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            text: _box.acceptText
            enabled: _box.type !== BAddressEditBox.Type.AddWatchOnly
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BStandardText.button.cancelRole
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
            text: BStandardText.button.resetRole
        }
    }

    onAboutToShow: {
        _box.forceActiveFocus()
    }
    onReset: {
        _box.reset()
    }
}
