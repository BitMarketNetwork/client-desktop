import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../js/functions.js" as Funcs

ExchangePanel {

    onTheLeft: true
    image: Funcs.loadImage("send_money.svg")
    title: qsTr("I am paying:")


}
