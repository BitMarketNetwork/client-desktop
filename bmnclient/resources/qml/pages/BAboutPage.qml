import QtQuick 2.15
import "../application"

BApplicationPage {
    id: _base

    title: qsTr("Application information")

    list.currentIndex: 0
    stack.currentIndex: 1

    BAboutGeneralPane {}

    Repeater {
        property string title: ""
        property string iconPath: ""
        enabled: false
        model: BBackend.coinList
        delegate: BAboutCoinPane {
            coin: model
        }
    }
}
