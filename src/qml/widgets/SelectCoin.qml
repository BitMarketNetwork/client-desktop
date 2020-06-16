import QtQuick 2.12
import "../controls"
import "../js/constants.js" as Const


Base {
    id: _no_selection_info
    anchors.fill: parent
    /*
    LogoImage {
        anchors{
            right: parent.right
            top: parent.top
            topMargin: 10
            rightMargin: 20
        }

        id: _main_logo
    }
    XemLine{
        anchors{
            top: _main_logo.bottom
            left: parent.left
            right: parent.right
            leftMargin: 60
            rightMargin: 60
            topMargin: 8
        }
        id: _coin_line
        blue: false
    }
    */
    TitleText {
        id: _select_coin
        text: qsTr("Select address from the list")
        anchors.centerIn: parent
        sub: true

    }
}
