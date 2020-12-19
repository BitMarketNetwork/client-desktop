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
            if (_box.type === BAddressEditBox.Type.AddWatchOnly) {
                // TODO offline validator, use clientlib
                // BBackend.coinManager.validateAddress(coinIndex, dialog.coinAddress)
                _acceptButton.enabled = (addressText.length > 10)
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
            text: BStandardText.buttonText.cancelRole
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
            text: BStandardText.buttonText.resetRole
        }
    }

    onAboutToShow: {
        _box.forceActiveFocus()
    }
    onReset: {
        _box.reset()
    }
}
