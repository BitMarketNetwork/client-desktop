import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"
import "../js/constants.js" as Constants


SendWidget {
    id: _base
    title: qsTr("Change:","New transction window")
    height: 80

    property alias newAddressLeft: _leftover.checked
    property alias leftOverAmount: _change_amount.amount
    property alias hasLeftOver: _leftover.vis


    MoneyCount{
        anchors{
            top: parent.top
            topMargin: 10
            margins: defMargin
            left: parent.left
            leftMargin: defLeftMargin
        }
        id: _change_amount
        unit: api.unit
        width: 300
    }
        MoneyCount{
            id: _fiat
            anchors{
                margins: defMargin
                verticalCenter: _change_amount.verticalCenter
                right: parent.right
            }
            unit: CoinApi.coins.currency
            width: 200
        }
        SwitchBox{
            id: _leftover
            anchors{
                top: _change_amount.bottom
                topMargin: 5
                left: _change_amount.left
            }
            text: qsTr("Send change to new address","New transction window")
            offText: qsTr("Return change to this address","New transction window")
            property bool vis: true
            onVisChanged: {
                _anim.from = vis?0:1
                _anim.to = vis?1:0
                _anim.running = true
            }

        PropertyAnimation{
            id: _anim
            property: "opacity"
            target: _leftover
            duration: 500
            onFinished: { }
        }

        }
}
