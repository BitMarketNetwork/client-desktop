import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"
import "../js/constants.js" as Constants


SendWidget {
    id: _base
    title: qsTr("Change:")
    height: 100

    property alias newAddressLeft: _leftover.checked
    property alias leftOverAmount: _change_amount.amount


    MoneyCount{
        anchors{
            top: parent.top
            topMargin: 20
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
                topMargin: 10
                left: _change_amount.left
            }
            text: qsTr("Send change on new address")
        }
}
