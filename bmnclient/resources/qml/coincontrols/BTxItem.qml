// JOK++
import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base
    property var tx // TxModel
    property BMenu contextMenu
    property real smallFontPointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small

    text: tx.hash

    contentItem: BColumnLayout {
        BRowLayout {
            BUnfoldToolButton {
                onCheckedChanged: {
                    _detailsLoader.showControl(checked)
                }
            }
            BColumnLayout {
                BLabel {
                    BLayout.fillWidth: true
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
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
                    font.pointSize: _base.smallFontPointSize
                    font.bold: true
                    text: BCommon.txStatusMap[_base.tx.state.status][0]
                    color: Material.color(BCommon.txStatusMap[_base.tx.state.status][1])
                }
                BAmountLabel {
                    BLayout.alignment: Qt.AlignVCenter | Qt.AlignRight
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
        Loader {
            id: _detailsLoader

            BLayout.fillWidth: true
            BLayout.minimumHeight: BLayout.preferredHeight
            BLayout.preferredHeight: 0
            BLayout.maximumHeight: BLayout.preferredHeight

            active: false
            sourceComponent: BTxItemDetailsPane {
                clip: true // for animation
                tx: _base.tx
            }

            onLoaded: {
                unfold()
            }

            NumberAnimation {
                id: _detailsAnimation
                target: _detailsLoader
                duration: _applicationStyle.animationDuration
                easing.type: Easing.InOutQuad
                property: "BLayout.preferredHeight"

                onFinished: {
                    if (to === 0) {
                        _detailsLoader.active = false
                    }
                }
            }

            function showControl(show) {
                _detailsAnimation.stop()
                if (show) {
                    if (status === Loader.Ready) {
                        unfold()
                    } else {
                        active = false // reset status to Loader.Null
                        active = true
                    }
                } else {
                    fold()
                }
            }

            function unfold() {
                _detailsAnimation.from = item.height
                _detailsAnimation.to = item.implicitHeight
                _detailsAnimation.restart()
            }

            function fold() {
                _detailsAnimation.from = item.height
                _detailsAnimation.to = 0
                _detailsAnimation.restart()
            }
        }
    }

    onDoubleClicked: {
        BBackend.uiManager.copyToClipboard(tx.hash)
    }

    // TODO right click
}
