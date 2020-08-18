import QtQuick 2.12

Base {
    id: _base
    property alias icon: _coin_label.icon
    property alias name: _coin_label.name
    property alias amount: _crypto.amount
    property alias unit: _crypto.unit
    property alias fiatAmount: _fiat.amount
    property alias fiatUnit: _fiat.unit
    property bool test: false



    readonly property int icon_size: 45
    antialiasing: true

    height: 60
    clip: true
        XemLine{
            id: _border
            anchors{
//                bottom: parent.bottom
                top: parent.top
                topMargin: 0
                horizontalCenter: parent.horizontalCenter
            }
            width: _base.width 
            blue: true
        }

    CoinLabel{
        anchors{
            left: parent.left
            leftMargin: 5
            verticalCenter: parent.verticalCenter
        }
        id: _coin_label
        color: test? palette.link :palette.mid
        enabled: _base.enabled
    }

    Base{

        anchors{
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: 30
        }
//        width: 200
        width: parent.width * 0.4
        height: 40


        MoneyCount{
            anchors{
                left: parent.left
                top: parent.top
            }
            id: _crypto

            visible: _base.enabled
            color: palette.mid
        }

        MoneyCount{
            anchors{
                left: parent.left
                bottom: parent.bottom
            }
            id: _fiat

            width: _crypto.width
            visible: _base.enabled
//            fontSize: 10
            color: palette.mid
        }
    }

}
