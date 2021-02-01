import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    readonly property string acceptDelayText: BStandardText.button.acceptRole + " (%1)"
    readonly property int acceptDelay: BBackend.isDebugMode ? 1 : 10

    title: // TODO move to MessageDialog
        "<font color=\"%1\">".arg(Material.color(Material.Red))
        + qsTr("IMPORTANT NOTE")
        + "</font>"

    contentItem: BDialogLayout {
        columns: 1
        BDialogDescription {
            id: _message
            text: qsTr(
                      "This is an alpha version of the current application and it does not guarantee stable operation or safety of your finances.\n\n"
                      + "Please use this version carefully for reference only, as it is intended for demonstration purposes only")
        }
    }

    footer: BDialogButtonBox {
        BButton {
            id: _acceptButton
            property TextMetrics textMetrics: TextMetrics {
                font: _acceptButton.font
                text: _base.acceptDelayText.arg(999)
            }

            BDialogButtonBox.buttonRole: BDialogButtonBox.AcceptRole
            implicitWidth: leftPadding + rightPadding + textMetrics.width
            text: _base.acceptDelayText.arg(_base.acceptDelay)
            enabled: false
        }
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BStandardText.button.declineRole
        }
    }

    onAboutToShow: {
        _acceptTimer.start()
    }

    Timer {
        id: _acceptTimer
        property int counter: _base.acceptDelay
        interval: 1000
        repeat: true

        onTriggered: {
            if (--counter === 0) {
                stop()
                _acceptButton.text = BStandardText.button.acceptRole
                _acceptButton.enabled = true
            } else {
                _acceptButton.text = acceptDelayText.arg(counter)
            }
        }
    }
}
