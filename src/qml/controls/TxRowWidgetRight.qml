import QtQuick 2.12
import "../js/functions.js" as Funcs

Base {
    property alias amount: _crypto_count.amount
    property alias unit: _crypto_count.unit
    property alias fiatAmount: _fiat_count.amount
    property alias fiatUnit: _fiat_count.unit

    MoneyCount{
        id: _crypto_count
        anchors{
//            right: parent.right
//            rightMargin: 10
            left: parent.left
//            verticalCenter: parent.verticalCenter
            bottom: parent.verticalCenter
            bottomMargin: 5
        }
        fontSize: 12
        width: rightWidth
//        state: "right"
        color: palette.text
    }

    MoneyCount{
        id: _fiat_count
        anchors{
//            right: parent.right
//            rightMargin: 10
            left: parent.left
//            bottom: parent.bottom
//            bottomMargin: 5
            top: parent.verticalCenter
            topMargin: 5
        }
        color: _crypto_count.color
        fontSize: _crypto_count.fontSize
        width: rightWidth
//        state: "right"
    }

}
