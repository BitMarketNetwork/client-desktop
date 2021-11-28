import QtQuick
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
