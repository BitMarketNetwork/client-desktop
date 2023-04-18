import QtQuick
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"
import "../dialogcontrols"

BDialog {
    id: _base
    readonly property string acceptDelayText: BCommon.button.acceptRole + " (%1)"
    readonly property int acceptDelay: BBackend.debug.isEnabled ? 1 : 10

    title:
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
            text: BCommon.button.declineRole
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
                _acceptButton.text = BCommon.button.acceptRole
                _acceptButton.enabled = true
                _acceptButton.forceActiveFocus(Qt.TabFocus)
            } else {
                _acceptButton.text = acceptDelayText.arg(counter)
            }
        }
    }
}
