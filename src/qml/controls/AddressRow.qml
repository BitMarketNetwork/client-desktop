import QtQuick 2.12
import QtGraphicalEffects 1.12
import "../controls"
import "../widgets"
import "../api"
import "../js/constants.js" as Const
import "../js/functions.js" as Funcs

Base {
    id: _base

    property string  name: ""
    property string  label: ""
    property alias  amount: _crypto.amount
    property alias  unit: _crypto.unit
    property alias  fiatAmount: _fiat.amount
    property alias  fiatUnit: _fiat.unit
    property bool selected: false
    property alias watchOnly: _id_sign.visible
    property alias updating: _refresh.visible

    height: 40
    anchors.left: parent.left
    anchors.right: parent.right
    anchors.leftMargin: 20
    anchors.rightMargin: 20

    signal click();
    signal rightClick(int ptx, int pty);

    Rectangle{
        id: rectangle
        anchors.fill: parent
        anchors.margins: 5

        color: _base.selected?palette.highlight:palette.base
        radius: 5
        antialiasing: true


        Image {
            id: _id_sign
            source: Funcs.loadImage("eye.svg")
            fillMode: Image.PreserveAspectFit
            smooth: false
            cache: true
            width:  visible? 25 : 0
            height: width
            sourceSize.width: width
            sourceSize.height: height
                anchors{
                        left: parent.left
                        leftMargin: 10
                        verticalCenter: parent.verticalCenter

                }

        }
            LabelText{
                id: _main
                anchors{
                        left: _id_sign.right
                        leftMargin: 5
                        verticalCenter: parent.verticalCenter
                        right: _crypto.left

                }
                color: _base.selected?palette.highlightedText:palette.mid
                font.pixelSize: 12
                text: _base.name
                clip: true
            }
            MoneyCount{
                id: _crypto
                width: 120
                anchors{
                        right: parent.right
                        rightMargin: 8
//                        top: parent.top
//                        topMargin: 5
                        verticalCenter: parent.verticalCenter
                }
                fontSize: 16
                color: _base.selected?palette.highlightedText:palette.mid
            }
            MoneyCount{
                id: _fiat
                width: 70
                visible: false
                anchors{
                        //right: parent.right
                        //rightMargin: 10
                        horizontalCenter: _crypto.horizontalCenter
                        bottom: parent.bottom
                        bottomMargin: 5
                }
                fontSize: 10
                color: _base.selected?palette.highlightedText:palette.mid
            }
        Image {
            id: _refresh
            source: Funcs.loadImage("refresh.svg")
            fillMode: Image.PreserveAspectFit
            smooth: false
            cache: true
            width: 12
            height: width
            sourceSize.width: width
            sourceSize.height: height
                anchors{
//                        left: _fiat.right
                        leftMargin: 5
                        verticalCenter: parent.verticalCenter
                        left: parent.right
//                        rightMargin: 3

                }

        }

        MouseArea{
            anchors.fill: parent
            propagateComposedEvents: false
            pressAndHoldInterval: 100
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: {
                if (mouse.button === Qt.RightButton) {
                    _base.rightClick( mouse.x + _base.x , mouse.y + _base.y );
                }
                else{
                    _base.click()
                }
            }
            onDoubleClicked: {
                CoinApi.ui.copyToClipboard(_base.name)
            }
        }
    }
        XemLine{
            id: _border
            anchors{
//                bottom: parent.bottom
                top: parent.top
                horizontalCenter: parent.horizontalCenter
            }
            width: _base.width * 0.5
            blue: false
        }

}
