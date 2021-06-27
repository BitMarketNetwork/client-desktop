import QtQuick 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    property int type: BSeedPhraseDialog.Type.Generate
    property bool readOnly: false
    property bool enableAccept: false
    readonly property string closeDelayText: BCommon.button.closeRole + " (%1)"
    readonly property int closeDelay: 10

    enum Type {
        Generate,
        Validate,
        Restore,
        Reveal
    }

    title: {
        switch (type) {
        case BSeedPhraseDialog.Type.Generate:
            return qsTr("Generate new seed phrase")
        case BSeedPhraseDialog.Type.Validate:
            return qsTr("Test yourself whether you memorized the seed phrase")
        case BSeedPhraseDialog.Type.Restore:
            return qsTr("Restore seed phrase")
        case BSeedPhraseDialog.Type.Reveal:
            return qsTr("Reveal seed phrase")
        }
    }
    contentItem: BDialogLayout {
        // TODO advanced description
        BDialogPromptLabel {
            text: "Seed phrase:"
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
                    return qsTr("Re-enter generated seed phrase")
                case BSeedPhraseDialog.Type.Restore:
                    return qsTr("Enter your seed phrase")
                }
            }

            readOnly: _base.readOnly
            selectByMouse: !_base.readOnly
            wrapMode: TextEdit.WordWrap
            text: _base.context.text

            font.bold: true
            font.pointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.huge
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
                enabled: _base.enableAccept
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

    onOpened: {
        _seedPhrase.forceActiveFocus()
    }

    onAboutToShow: {
        switch (type) {
        case BSeedPhraseDialog.Type.Generate:
            break
        case BSeedPhraseDialog.Type.Validate:
        case BSeedPhraseDialog.Type.Restore:
            _seedPhrase.clear()
            break
        case BSeedPhraseDialog.Type.Reveal:
            _closeTimer.start()
            break
        }
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
