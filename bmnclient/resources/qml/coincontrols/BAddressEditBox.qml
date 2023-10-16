import "../application"
import "../basiccontrols"
import "../dialogcontrols"

BDialogLayout {
    id: _base

    // TODO: reimplement without dialog controls

    enum Type {
        Create,
        View,

        CreateRecipient,
        ViewRecipient,

        CreateWatchOnly
    }

    property var coin // CoinModel
    property int type: BAddressEditBox.Type.View
    property bool readOnly: _base.type === BAddressEditBox.Type.ViewRecipient || _base.type === BAddressEditBox.Type.View

    property alias addressNameText: _address.text
    property alias labelText: _label.text
    property alias commentText: _comment.text
    property alias isSegwit: _segwitSwitch.checked

    property string dialogTitleText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Create:
            return qsTr("Create new address")
        case BAddressEditBox.Type.View:
            return qsTr("Address information")
        case BAddressEditBox.Type.CreateRecipient:
            return qsTr("Create recipient address")
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Recipient address information")
        case BAddressEditBox.Type.CreateWatchOnly:
            return qsTr("Add Watch-Only Address")
        }
    }
    property string descriptionText: {
        switch (_base.type) {
        case BAddressEditBox.Type.CreateWatchOnly:
            return qsTr(
                        "Impossible to make transactions with this address.\n"
                        + "You can check the balance and view transactions only.")
        default:
            return ""
        }
    }

    property string addressPromptText: {
        switch (_base.type) {
        case BAddressEditBox.Type.CreateRecipient:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Recipient address:")
        default:
            return qsTr("Address:")
        }
    }
    property string addressPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Create:
        case BAddressEditBox.Type.CreateRecipient:
            return qsTr("Not created")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return ""
        case BAddressEditBox.Type.CreateWatchOnly:
            return qsTr("Enter watch-only address")
        }
    }

    property string segwitPromptText: qsTr("Segwit:")

    property string labelPromptText: qsTr("Label:")
    property string labelPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Create:
        case BAddressEditBox.Type.CreateRecipient:
            return qsTr("Enter label for new address (optional)")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return ""
        case BAddressEditBox.Type.CreateWatchOnly:
            return qsTr("Enter label for address (optional)")
        }
    }

    property string commentPromptText: qsTr("Comment:")
    property string commentPlaceholderText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Create:
        case BAddressEditBox.Type.CreateRecipient:
            return qsTr("Enter comment for new address (optional)")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return ""
        case BAddressEditBox.Type.CreateWatchOnly:
            return qsTr("Enter comment for address (optional)")
        }
    }

    property string acceptText: {
        switch (_base.type) {
        case BAddressEditBox.Type.Create:
        case BAddressEditBox.Type.CreateRecipient:
            return qsTr("Create address")
        case BAddressEditBox.Type.View:
        case BAddressEditBox.Type.ViewRecipient:
            return qsTr("Copy address")
        case BAddressEditBox.Type.CreateWatchOnly:
            return BCommon.button.addRole
        }
    }

    BDialogDescription {
        id: _description
        text: _base.descriptionText
        visible: text.length > 0
    }
    BDialogSeparator {
        visible: _description.visible
    }

    BDialogPromptLabel {
        text: qsTr("Coin:")
    }
    BDialogInputLabel {
        text: _base.coin.fullName
    }

    BDialogSeparator {}

    BDialogPromptLabel {
        text: _base.addressPromptText
    }
    BDialogInputTextField {
        id: _address
        enabled: _base.type !== BAddressEditBox.Type.Create && _base.type !== BAddressEditBox.Type.CreateRecipient
        readOnly: _base.readOnly
        placeholderText: _base.addressPlaceholderText
    }
    // TODO validator "✔", "✘"

    BDialogPromptLabel {
        visible: _base.type !== BAddressEditBox.Type.CreateWatchOnly
        text: _base.segwitPromptText
    }
    BDialogInputSwitch {
        enabled: !_base.readOnly
        id: _segwitSwitch
        visible: _base.type !== BAddressEditBox.Type.CreateWatchOnly
        checked: true
    }

    BDialogSeparator {}

    BDialogPromptLabel {
        text: _base.labelPromptText
    }
    BDialogInputTextField {
        id: _label
        readOnly: _base.readOnly
        placeholderText: _base.labelPlaceholderText
        maximumLength: 32
    }

    BDialogPromptLabel {
        text: _base.commentPromptText
    }
    BDialogInputTextArea {
        id: _comment
        readOnly: _base.readOnly
        visibleLineCount: 6
        placeholderText: _base.commentPlaceholderText
    }

    onActiveFocusChanged: {
        if (activeFocus) {
            switch (_base.type) {
            case BAddressEditBox.Type.Create:
            case BAddressEditBox.Type.CreateRecipient:
                _label.forceActiveFocus(Qt.TabFocus)
                break
            default:
                _address.forceActiveFocus(Qt.TabFocus)
                break
            }
        }
    }

    function clear() {
        if (!readOnly) {
            addressNameText = ""
            isSegwit = true
            labelText = ""
            commentText = ""
        }
    }
}
