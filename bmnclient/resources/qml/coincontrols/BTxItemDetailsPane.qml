import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property var tx // TxModel

    Material.elevation: 1 // for background, view QtQuick/Controls.2/Material/Pane.qml
    padding: _applicationStyle.padding
    contentItem: BInfoLayout {
        BInfoLabel {
            text: qsTr("Height:")
        }
        BInfoValue {
            text: _base.tx.state.heightHuman
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Confirmations:")
        }
        BInfoValue {
            text: _base.tx.state.confirmationsHuman
        }
        BInfoSeparator {}

        BInfoLabel {
            text: qsTr("Fee:")
        }
        BAmountInfoValue {
            amount: _base.tx.feeAmount
        }
        BInfoSeparator {}

        BTxIoView {
            BLayout.columnSpan: parent.columns
            BLayout.fillWidth: true
            tx: _base.tx
        }
        BInfoSeparator {}
    }
}
