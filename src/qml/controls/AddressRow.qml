import QtQuick 2.12
import QtGraphicalEffects 1.12
import "../controls"
import "../widgets"
import "../api"
import "../js/constants.js" as Const

Base {
    id: _base

    property string  name: ""
    property string  label: ""
    property alias  amount: _crypto.amount
    property alias  unit: _crypto.unit
    property alias  fiatAmount: _fiat.amount
    property alias  fiatUnit: _fiat.unit
    property bool selected: false

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


            LabelText{
                id: _main
                anchors{
                        left: parent.left
                        leftMargin: 10
                        verticalCenter: parent.verticalCenter

                }
                color: _base.selected?palette.highlightedText:palette.mid
                font.pixelSize: 14
                text: _base.name
            }
            LabelText{
                id: _sub
                visible: false
                anchors{
                        leftMargin: 10
                        bottom: _main.bottom
                        right: _crypto.left
                        rightMargin: 10
                }
                color: _base.selected?palette.highlightedText:palette.mid
                font.pixelSize: 10
                text: _base.name
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
