import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

import "../js/functions.js" as Funcs

ExchangePanel {
    onTheLeft: false
    image: Funcs.loadImage("receive_money.svg")
    title: qsTr("I will receive:")
}
