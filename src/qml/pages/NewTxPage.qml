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

    onValidChanged:{
        console.log("TX VALID" + valid)
    }

    default property alias content: _content.children
    antialiasing: true

    Component.onCompleted:{
        console.log("COIN NAME",_base.coinName)
    }

    readonly property int txMargin: 10

    signal accept()
    signal cancel()


    Rectangle{
//    Rectangle{
        id: _area
        width: 750
        height: 300
        anchors{
//            horizontalCenter: parent.horizontalCenter
            left: parent.left
            top: parent.top
            bottom: parent.bottom
        }
//        color: palette.base
//        clip: true
//        ScrollBar.vertical.policy: ScrollBar.AlwaysOn
        /*
        gradient: LinearBg{
            colorOne: palette.base
            colorTwo: palette.mid
        }
        */
        TxBigButton{
            id: _back_btn
            anchors{
                top: _area.top
                right: _area.right
                margins: txMargin
//                topMargin: defaultMargin
            }
            text: qsTr("Back")
            icon.source: Funcs.loadImage("left_arrow.png")
            display: Button.TextBesideIcon
            onClicked: {
                cancel()
                _base.popPage()
            }
        }

        Column{
            id: _header
            anchors{
                    left: parent.left
                    right: parent.right
                    top: parent.top
                    bottom: _action_btn.top
                    topMargin: defaultMargin
                    margins: 10
            }
            spacing: txMargin

            TitleText{
                id: _action_name
//                height: 30
                leftPadding: 10
            }

            Base{
                anchors{
                    left: parent.left
                    right: parent.right
                }
                height: 30
                /*
                LabelText{
                    id: _currency
                    anchors{
                        left: parent.left
                        verticalCenter: parent.verticalCenter
                    }
                    text: qsTr("Currency:")
                    width: 114
                }
                */
                CoinLabel{
                    anchors{
//                        left: _currency.right
                        left: parent.left
                        verticalCenter: parent.verticalCenter
                    }
                    id: _coin_label
                    color: palette.text

                    Component.onCompleted: {
                        console.log(coinIcon)
                    }
                }
            }
            Base{
                anchors{
                    left: parent.left
                    right: parent.right
                }
                id: _content
                height: childrenRect.height
            }
        }
        BigBlueButton{
            anchors{
                bottom: parent.bottom
                margins: 5
//                horizontalCenter: parent.horizontalCenter
                left: _header.left
                right: _header.right
            }
            id: _action_btn
            text: _action_name.text
            pale: true
            onClicked: {
                accept()
            }
        }

    }

}

