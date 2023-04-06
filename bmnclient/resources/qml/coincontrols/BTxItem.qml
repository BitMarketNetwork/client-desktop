import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var tx // TxModel
    property BMenu contextMenu
    property real smallFontPointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small

    text: tx.name

    contentItem: BSpoilerItem {
        headerItem: BRowLayout {
            BColumnLayout {
                BLabel {
                    Layout.fillWidth: true
                    elide: BLabel.ElideMiddle
                    font.bold: true
                    text: _base.text
                }
                BLabel {
                    font.pointSize: _base.smallFontPointSize
                    text: _base.tx.state.timeHuman
                }
            }
            BColumnLayout {
                BLabel {
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    font.pointSize: _base.smallFontPointSize
                    font.bold: true
                    text: BCommon.txStatusMap[_base.tx.state.status][0]
                    color: Material.color(BCommon.txStatusMap[_base.tx.state.status][1])
                }
                BAmountLabel {
                    Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    font.pointSize: _base.smallFontPointSize
                    amount: _base.tx.amount
                }
            }
            /* TODO BContextMenuToolButton {
                onClicked: {
                    _base.contextMenu.tx = _base.tx
                    toggleMenu(_base.contextMenu)
                }
            }*/
        }
        contentItem: BTxItemDetailsPane {
            clip: true // for animation
            tx: _base.tx
        }
    }

    onDoubleClicked: {
        BBackend.clipboard.text = tx.name
    }

    // TODO right click
}
