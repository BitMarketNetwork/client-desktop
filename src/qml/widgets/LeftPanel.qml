import QtQuick 2.12
import "../controls"
import "../js/functions.js" as Funcs


//ParticleBg {
//ClickBg {
Item{
    id: _base

    property int index: 0

    width: 120
    antialiasing: true

    signal walletClick()
    signal exchangeClick()

    /*
    gradient: LinearBg{
        colorOne: palette.base
        colorTwo: palette.shadow
    }
    */


    Column{
        anchors{
            top: parent.top
            horizontalCenter: parent.horizontalCenter
            margins: 20
        }

        spacing: 10

        LeftMenuItem{
            id: _wallet_item
            icon: Funcs.loadImage("wallet-solid.png")
            text: qsTr("Wallet")
            selected: 0 === index
            onClicked: {
                index = 0  ;
                walletClick();
            }
        }

        LeftMenuItem{
            id: _exchange_item
            icon: Funcs.loadImage("exchange-alt-solid.png")
            text: qsTr("Exchange")
            selected: 1 === index
            enabled: false
            onClicked: {
                index = 1;
                exchangeClick();
            }
        }

        LeftMenuItem{
            id: _market_item
            icon: Funcs.loadImage("markets.png")
            text: qsTr("Markets")
            selected: 2 === index

            enabled: false
            onClicked: {
                index = 2;
            }
        }
    }

}
