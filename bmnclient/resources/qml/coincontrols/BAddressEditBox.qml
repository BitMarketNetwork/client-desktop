import "../application"
import "../basiccontrols"

BControl {
    id: _base
    default property alias content: _layout.children

    enum Type {
        Generate,
        View,

        GenerateRecipient,
        ViewRecipient,

        AddWatchOnly
    }

    property BCoinObject coin: null
    property int type: BAddressEditBox.Type.View
    property bool readOnly: _base.type === BAddressEditBox.Type.ViewRecipient || _base.type === BAddressEditBox.Type.View

    property alias addressText: _address.text
    property alias labelText: _label.text
    property alias commentText: _comment.text
    property alias useSegwit: _segwitSwitch.checked

    property string dialogTitleText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Generate:
            return qsTr("Generate new address")
        case BAddressEditBox.Type.View:
            return qsTr("Address information")
        case BAddressEditBox.Type.GenerateRecipient:
            return qsTr("Generate recipient address")
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Recipient address information")
        case BAddressEditBox.Type.AddWatchOnly:
            return qsTr("Add Watch-Only Address")
        }
    }
    property string descriptionText: {
        switch (_base.type) {
        case BAddressEditBox.Type.AddWatchOnly:
            return qsTr(
                        "Impossible to make transactions with this address.\n"
                        + "You can check the balance and view transactions only.")
        default:
            return ""
        }
    }

    property string addressPromtText: {
        switch (_base.type) {
        case BAddressEditBox.Type.GenerateRecipient:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Recipient address:")
        default:
            return qsTr("Address:")
        }
    }
    property string addressPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Generate:
        case BAddressEditBox.Type.GenerateRecipient:
            return qsTr("Not generated")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("None")
        case BAddressEditBox.Type.AddWatchOnly:
            return qsTr("Enter watch-only address")
        }
    }

    property string segwitPromtText: qsTr("Segwit:")

    property string labelPromtText: qsTr("Label:")
    property string labelPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Generate:
        case BAddressEditBox.Type.GenerateRecipient:
            return qsTr("Enter label for new address (optional)")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("None")
        case BAddressEditBox.Type.AddWatchOnly:
            return qsTr("Enter label for address (optional)")
        }
    }

    property string commentPromtText: qsTr("Comment:")
    property string commentPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Generate:
        case BAddressEditBox.Type.GenerateRecipient:
            return qsTr("Enter comment for new address (optional)")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("None")
        case BAddressEditBox.Type.AddWatchOnly:
            return qsTr("Enter comment for address (optional)")
        }
    }

    property string acceptText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Generate:
        case BAddressEditBox.Type.GenerateRecipient:
            return qsTr("Generate address")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Copy address")
        case BAddressEditBox.Type.AddWatchOnly:
            return BStandardText.buttonText.addRole
        }
    }

    contentItem: BDialogLayout {
        id: _layout

        BDialogDescription {
            id: _description
            text: _base.descriptionText
            visible: text.length > 0
        }
        BDialogSeparator {
            visible: _description.visible
        }

        BDialogPromtLabel {
            text: qsTr("Coin:")
        }
        BDialogInputLabel {
            text: _base.coin.name
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: _base.addressPromtText
        }
        BDialogInputTextField {
            id: _address
            enabled: _base.type !== BAddressEditBox.Type.Generate && _base.type !== BAddressEditBox.Type.GenerateRecipient
            readOnly: _base.readOnly
            placeholderText: _base.addressPlaceholderText
        }
        // TODO validator "✔", "✘"

        BDialogPromtLabel {
            visible: _base.type !== BAddressEditBox.Type.AddWatchOnly
            text: _base.segwitPromtText
        }
        BDialogInputSwitch {
            enabled: !_base.readOnly
            id: _segwitSwitch
            visible: _base.type !== BAddressEditBox.Type.AddWatchOnly
            checked: true
        }

        BDialogSeparator {}

        BDialogPromtLabel {
            text: _base.labelPromtText
        }
        BDialogInputTextField {
            id: _label
            readOnly: _base.readOnly
            placeholderText: _base.labelPlaceholderText
        }

        BDialogPromtLabel {
            text: _base.commentPromtText
        }
        BDialogInputTextArea {
            id: _comment
            readOnly: _base.readOnly
            visibleLineCount: 6
            placeholderText: _base.commentPlaceholderText
        }
    }

    onActiveFocusChanged: {
        if (activeFocus) {
            switch (_base.type) {
            case BAddressEditBox.Type.Generate:
            case BAddressEditBox.Type.GenerateRecipient:
                _label.forceActiveFocus()
                break
            default:
                _address.forceActiveFocus()
                break
            }
        }
    }

    function reset() {
        if (!readOnly) {
            addressText = ""
            useSegwit = true
            labelText = ""
            commentText = ""
        }
    }
}
