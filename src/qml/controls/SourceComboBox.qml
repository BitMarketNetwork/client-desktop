import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"

ComboBox {
    id: _base

    //  property alias notEditable: _input.readOnly
     property bool notEditable: false

    height: 30

    spacing: 5
    leftPadding: 5
    rightPadding: 30

    signal click()


    textRole: "name"
    font: simpleFont

    contentItem: Text {
        leftPadding: 0
        rightPadding: _base.indicator.width + _base.spacing

        text: qsTr("Select source addresses:")
        font: _base.font
        color: _base.enabled? palette.text: palette.mid
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    delegate: Item {
                width: _base.width
                height: 30

                CheckDelegate {
                    id: _del
                    width: parent.width
                    height: 30
                    text: qsTr("%1 (%2 %3)").arg(modelData.name).arg(CoinApi.settings.coinBalance(modelData.balance)).arg(CoinApi.coins.unit)
                    highlighted: false
                    checked: _auto.checked || modelData.useAsSource
                    onCheckedChanged: {
                        modelData.useAsSource = checked
                        click()
                    }
                    enabled: !_auto.checked

                    indicator: CheckBoxIndicator{
                        x: parent.width - 30
                        bgColor: palette.mid
                        fgColor: _del.enabled ? palette.text: palette.mid
                        color: palette.base
                        checked: parent.checked
                    }
                }
            }
    background: Rectangle{
        color: palette.base
        border{
            width: 1
            color: palette.text
        }
    }

    popup: Popup {
        y: _base.height - 1
        width: _base.width
        implicitHeight: contentItem.implicitHeight
        padding: 1

        contentItem: Item{
            width: _base.width
            implicitHeight: _auto.implicitHeight + _list.implicitHeight + 30

            Switch{
                id: _auto
                text: qsTr("Auto selection")
                // contentItem: Text{
                //     text: _auto.text
                //     color: palette.text
                //     x: 100
                // }

                font{
                    bold: _auto.checked
                }
                spacing: 20


                anchors{
                    top: parent.top
//                    horizontalCenter: parent.horizontalCenter
                    left: parent.left
                    right: parent.right
                    margins: 10
                }
                background: Base{
//                    color: palette.midlight
//                    border{ width: 1  }
//                    radius: 1
                }
            }

            XemLine{
                anchors{
                    bottom: _auto.bottom
                    left: parent.left
                    right: parent.right
                    margins: 10
                    bottomMargin: 0
                }
                blue: false
            }

            ListView {
                id: _list
                anchors{
                    top: _auto.bottom
                    margins: 10
                }

                clip: true
                implicitHeight: contentHeight
                width: parent.width
                model: _base.popup.visible ? _base.delegateModel : null

                ScrollIndicator.vertical: ScrollIndicator { }
            }
        }

        background: Rectangle {
            border.color: palette.mid
            radius: 2
        }
    }
}
