import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"
import "../js/constants.js" as Constants

BasePage {
    id: _base

    property alias action: _action_name.text
    property alias actionIcon: _action_btn.icon.source
    property alias coinName: _coin_label.name
    property alias coinIcon: _coin_label.icon
    property alias valid: _action_btn.enabled
    property alias bottomY: _bottom_row.y
    property alias titleHeight: _action_name.height

    default property alias content: _content.children


    signal accept()
    signal cancel()




        CoinLabel{
            id: _coin_label
            width: 200
                    anchors{
                        left: parent.left
                        verticalCenter: _action_name.verticalCenter
                        margins: 20
                    }

            color: palette.text
        }

        TitleText{
            id: _action_name
                    anchors{
                        top: parent.top
                        right: parent.right
                        rightMargin: (rightSpaceFactor + 0.1 )* parent.width
                        margins: 20
                    }
//                    sub: true
                    rightPadding: 20
        }
        XemLine{
            width: _base.width
            anchors{
                bottom: _content.top
                left: _content.left
                right: _content.right
//                margins: 10
//                bottomMargin: 0
            }
        }
        Base{
            id: _content


            anchors{
                top: _action_name.bottom
                left: parent.left
                right: parent.right
                rightMargin: rightSpaceFactor * parent.width
                margins: 10
            }
        }
        Rectangle{
            id: _bottom_row
            color: palette.base
            radius: 2
            anchors{
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                rightMargin: rightSpaceFactor * parent.width
                margins: 10
            }
            height: 50
            BigBlueButton{
                id: _action_btn
                anchors{
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    margins: 10
                }
                width: parent.width * 0.66
                text: _action_name.text
                onClicked: {
                    // _base.popPage()
                    accept()
                }
            }
            TxBigButton{
                id: _back_btn
                    anchors{
                        verticalCenter: parent.verticalCenter
                        right: parent.right
                        margins: 10
                    }
                text: qsTr("Back")
                icon.source: Funcs.loadImage("left_arrow.png")
                display: Button.TextBesideIcon
                onClicked: {
                    cancel()
                    _base.popPage()
                }
            }
        }
}
