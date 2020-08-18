import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../js/functions.js" as Funcs

Base{
    property alias coinName: _coin_row.text
    property alias coinIcon: _coin_icon.source
    property alias amount: _crypto.amount
    property alias fiatAmount: _fiat.amount

    anchors{
        left: parent.left
        right: parent.right
    }

    Row{

        anchors{
            fill: parent
        }
        spacing: 10

        Image {
            id: _coin_icon
            anchors{
                verticalCenter: parent.verticalCenter
            }
            sourceSize.height: width
            sourceSize.width: width
            source: Funcs.loadImage("btc_icon.png")
            height: width
            width: 45
            fillMode: Image.PreserveAspectFit
            smooth: true
        }
        LabelText{
            id: _coin_row
            anchors{
        //                    top: parent.top
        //                    horizontalCenter: parent.horizontalCenter
        //                    horizontalCenterOffset: -20
                verticalCenter: _coin_icon.verticalCenter
            }
            width: 100
        }

    }
        MoneyCount{
            anchors{
                verticalCenter: parent.verticalCenter
                horizontalCenter: parent.horizontalCenter
            }
            id: _crypto
            color: palette.text
            unit: api.unit
            fontSize: 20
            amounFontSize: 30
            width: 100
        }

        MoneyCount{
            anchors{
                verticalCenter: parent.verticalCenter
                right: parent.right
            }
            id: _fiat
            color: palette.text
            unit: api.currency
            fontSize: 14
            amounFontSize: 20
            width: 100
        }
    XemLine{
        anchors{
            top: parent.bottom
        }
        id: _coin_line
        blue: false
        width: parent.width
    }
}
