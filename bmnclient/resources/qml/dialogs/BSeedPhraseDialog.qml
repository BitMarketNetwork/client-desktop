import QtQuick
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    property int type: BSeedPhraseDialog.Type.Generate
    property bool readOnly: false
    readonly property string closeDelayText: BCommon.button.closeRole + " (%1)"
    readonly property int closeDelay: 10
    signal phraseChanged(string value)
    signal seedPhraseAccepted(string wallet_name, string seed_password)

    enum Type {
        Generate,
        Validate,
        Restore,
        Reveal
    }

    title: {
        switch (type) {
        case BSeedPhraseDialog.Type.Generate:
            return qsTr("Generate new Seed Phrase")
        case BSeedPhraseDialog.Type.Validate:
            return qsTr("Validate new Seed Phrase")
        case BSeedPhraseDialog.Type.Restore:
            return qsTr("Restore Seed Phrase")
        case BSeedPhraseDialog.Type.Reveal:
            return qsTr("Reveal Seed Phrase")
        }
    }
    contentItem: BDialogLayout {
        // TODO advanced description
        BDialogPromptLabel {
            visible: _base.type === BSeedPhraseDialog.Type.Restore || _base.type === BSeedPhraseDialog.Type.Validate
            text: qsTr("Wallet name:")
        }
        BDialogInputTextField {
            id: _walletName
            maximumLength: 32
            visible: _base.type === BSeedPhraseDialog.Type.Restore || _base.type === BSeedPhraseDialog.Type.Validate
            placeholderText: qsTr("Enter name")
            text: qsTr("New wallet")
            validator: BBackend.keyStore.nameValidator
        }

        BDialogPromptLabel {
            text: qsTr("Seed Phrase:")
        }
        BDialogInputTextArea {
            id: _seedPhrase
            visibleLineCount: 10
            placeholderText: {
                switch (_base.type) {
                case BSeedPhraseDialog.Type.Generate:
                case BSeedPhraseDialog.Type.Reveal:
                    return qsTr("None")
                case BSeedPhraseDialog.Type.Validate:
                    return qsTr("Re-enter generated Seed Phrase")
                case BSeedPhraseDialog.Type.Restore:
                    return qsTr("Enter your Seed Phrase")
                }
            }

            readOnly: _base.readOnly
            selectByMouse: !_base.readOnly
            wrapMode: TextEdit.WordWrap
            text: _base.context.text

            font.bold: true
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge

            onTextChanged: {
                _base.phraseChanged(text)
                if (text.length > 0 && _base.type === BSeedPhraseDialog.Type.Reveal) {
                    _closeTimer.start()
                }
            }
        }
        BDialogSeparator{}
        BSpoilerItem {
            id: _spoiler
            BLayout.columnSpan: parent.columns
            visible: _base.type === BSeedPhraseDialog.Type.Restore || _base.type === BSeedPhraseDialog.Type.Validate

            headerItem: BRowLayout {
                BLabel {
                    text: qsTr("Seed's password (optional)")
                }
            }
            contentItem: BDialogLayout {
                columns: 2
                property alias password: _seedPassword.text
                BDialogPromptLabel {
                    text: qsTr("Seed's password:")
                }
                BDialogInputTextField {
                    id: _seedPassword
                    echoMode: _showPassword.checked ? BTextField.Normal : BTextField.Password
                    placeholderText: qsTr("Enter your password")
                }

                BDialogPromptLabel {
                    text: qsTr("Show password:")
                }
                BDialogInputSwitch {
                    id: _showPassword
                    BLayout.columnSpan: parent.columns - 1
                }
            }
        }
    }
    footer: BDialogButtonBox {
        id: _buttonBox
        Loader {
            active: _base.type !== BSeedPhraseDialog.Type.Reveal
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
                parent: _buttonBox
                text: BCommon.button.continueRole
                enabled: _base.context.isValid && _walletName.length > 0
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
        BButton {
            id: _closeButton
            property TextMetrics textMetrics: TextMetrics {
                font: _closeButton.font
                text: closeDelayText.arg(999)
            }

            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: {
                switch (_base.type) {
                case BSeedPhraseDialog.Type.Generate:
                case BSeedPhraseDialog.Type.Validate:
                case BSeedPhraseDialog.Type.Restore:
                    return BCommon.button.cancelRole
                case BSeedPhraseDialog.Type.Reveal:
                    return _base.closeDelayText.arg(_base.closeDelay)
                }
            }

            Component.onCompleted: {
                if (_base.type === BSeedPhraseDialog.Type.Reveal) {
                    implicitWidth = leftPadding + rightPadding + textMetrics.width
                }
            }
        }
        Loader {
            active: _base.type !== BSeedPhraseDialog.Type.Reveal
            sourceComponent: BButton {
                BDialogButtonBox.buttonRole: BDialogButtonBox.ResetRole
                text: {
                    switch (_base.type) {
                    case BSeedPhraseDialog.Type.Generate:
                        return BCommon.button.refreshRole
                    case BSeedPhraseDialog.Type.Validate:
                    case BSeedPhraseDialog.Type.Restore:
                        return BCommon.button.resetRole
                    case BSeedPhraseDialog.Type.Reveal:
                        return ""
                    }
                }
            }
            onLoaded: {
                _buttonBox.addItem(item)
            }
        }
    }

    onAccepted: {
        if (_base.type === BSeedPhraseDialog.Type.Restore || _base.type === BSeedPhraseDialog.Type.Validate)
            _base.seedPhraseAccepted(
                _walletName.text,
                _spoiler.content ? _spoiler.content.password : "")
    }
    onReset: {
        switch (type) {
        case BSeedPhraseDialog.Type.Generate:
            break
        case BSeedPhraseDialog.Type.Validate:
        case BSeedPhraseDialog.Type.Restore:
            _seedPhrase.clear()
            break
        case BSeedPhraseDialog.Type.Reveal:
            break
        }
    }

    Timer {
        id: _closeTimer
        property int counter: _base.closeDelay
        interval: 1000
        repeat: true

        onTriggered: {
            if (--counter === 0) {
                stop()
                _seedPhrase.clear()
                _base.reject()
            } else {
                _closeButton.text = _base.closeDelayText.arg(counter)
            }
        }
    }
}
