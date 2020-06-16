import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"
import "../controls"

import "../js/functions.js" as Funcs
import "../js/constants.js" as Constants

SendWidget {

    id: _base
    title: qsTr("Amount:")
    height: 110

    titleColor: valid? palette.text: palette.brightText

    property alias amount: _value.amount
    property alias fiatAmount: _fiat.amount
    property real 	maximum: 0
    property alias maxLength: _value.maxLength
    property bool valid: True


    signal max()
    signal less()
    signal more()
    signal edit(string value)

    TxButton{
        id: _max_btn
        text: qsTr("Max")
        anchors{
            margins: defMargin
//            bottomMargin: 10
            bottom: parent.bottom
//            left: parent.left
            right: parent.right
        }
        onClicked: max()
        height: 30
        width: 100
        // TODO: not good to have many instances!!
        /*
        ToolTip{
            delay: Constants.tooltipDelay
            visible: _max_btn.hovered
            text: qsTr("Send all amount avialable")
        }
        */
    }

    MoneyCountInput{
        anchors{
            top: parent.top
            topMargin: 20
            right: parent.right
            margins: defMargin
            left: parent.left
            leftMargin: defLeftMargin
        }
        id: _value
        amount: "0.002"
        unit: CoinApi.coins.coin.unit
        color: valid? palette.mid : palette.brightText
        onWheelDown: {
            less()
        }
        onWheelUp: {
            more()
        }

        onEdit:{
            _base.edit(amount)
        }
    }
    MoneyCount{
        anchors{
            top: _value.bottom
            topMargin: 10
            left: _value.left
            bottom: _max_btn.bottom
        }
        id: _fiat
        width: _value.amoutWidth
        amount: api.address.balanceHuman
        unit: api.currency
//        horAlignment: Text.AlignHCenter
    }
}
