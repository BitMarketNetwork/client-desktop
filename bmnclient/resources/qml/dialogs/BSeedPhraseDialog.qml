import QtQuick 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base

    enum Type {
        Generate,
        Validate,
        Restore,
        Reveal
    }

    property int type: BSeedPhraseDialog.Type.Generate
    property alias seedPhraseText: _seedPhrase.text
    property bool readOnly: false
    property bool enableAccept: false

    readonly property string closeDelayText: BStandardText.button.closeRole + " (%1)"
    readonly property int closeDelay: 10

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
        BDialogPromtLabel {
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
                text: BStandardText.button.continueRole
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
                    return BStandardText.button.cancelRole
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
                        return BStandardText.button.refreshRole
                    case BSeedPhraseDialog.Type.Validate:
                    case BSeedPhraseDialog.Type.Restore:
                        return BStandardText.button.resetRole
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

    onAboutToShow: {
        _seedPhrase.forceActiveFocus()
        switch (type) {
        case BSeedPhraseDialog.Type.Generate:
            if (!_saltDialogLoader.active) {
                _saltDialogLoader.active = true
                Qt.callLater(_saltDialogLoader.item.open)
            }
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
            _saltDialogLoader.item.open()
            break
        case BSeedPhraseDialog.Type.Validate:
        case BSeedPhraseDialog.Type.Restore:
            _seedPhrase.clear()
            break
        case BSeedPhraseDialog.Type.Reveal:
            break
        }
    }

    onRejected: {
        _saltDialogLoader.active = false
    }

    Loader {
        id: _saltDialogLoader
        active: false
        sourceComponent: BSeedSaltDialog {
            property bool used: false

            onAboutToShow: {
                _seedPhrase.text = BBackend.keyStore.prepareGenerateSeedPhrase(null)
            }
            onUpdateSalt: {
                _seedPhrase.text = BBackend.keyStore.updateGenerateSeedPhrase(value)
            }
            onAccepted: {
                _seedPhrase.forceActiveFocus()
            }
            onRejected: {
                _base.reject()
            }
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
