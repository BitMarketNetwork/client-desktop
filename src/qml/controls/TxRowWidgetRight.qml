import QtQuick 2.12
import "../js/functions.js" as Funcs

Base {
    property alias amount: _crypto_count.amount
    property alias statusText: _status.text
    property alias statusColor: _status.color
    property alias unit: _crypto_count.unit
    property alias fiatAmount: _fiat_count.amount
    property alias fiatUnit: _fiat_count.unit

    Column{
        anchors{
            fill: parent
        }
        spacing: 1
    Text {
        id: _status
        anchors{
            left: parent.left
//            leftMargin: 10
        }
        font{
            pixelSize: 14
        }

        width: rightWidth
    }

    MoneyCount{
        id: _crypto_count
        anchors{
            left: parent.left
        }
        fontSize: 12
        width: rightWidth
        color: palette.text
    }

    MoneyCount{
        id: _fiat_count
        anchors{
            left: parent.left
        }
        fontSize: _crypto_count.fontSize
        width: rightWidth
    }
    }

}
