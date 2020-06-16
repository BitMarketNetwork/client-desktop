import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

import "../js/functions.js" as Funcs
import "../js/constants.js" as Const

ToolBar {

    signal about();
    signal quit();
    signal settings();
    signal exportAddress()
    signal newAddress()
    signal addWatchAddress()
    signal showEmpty(bool show)


    property alias showEmptyValue: _show_empty.checked

    height: Const.xemBtnHeight + 20

    Row{
        spacing: 5
        anchors{
            top: parent.top
            bottom: parent.bottom
            left: _divider.right
            leftMargin: 40
            margins: 10
        }

        ToolItem{
            text: qsTr("Export")
            pix: Funcs.loadImage("export.svg")
            onClicked: exportAddress()
        }
        ToolItem{
            text: qsTr("New address")
            pix: Funcs.loadImage("new_wallet.png")
            onClicked: newAddress()
        }
        ToolItem{
            id: _show_empty
            text: qsTr("Show empty")
            pix: Funcs.loadImage("no-money.svg")
            checkable: true
            onCheckedChanged: {
                showEmpty(checked)
            }
        }
        /*
        ToolItem{
            text: qsTr("Add watch-only address")
            pix: Funcs.loadImage("new_wallet.png")
            onClicked: addWatchAddress()
            overlayColor: palette.shadow
        }
        */
        ToolItem{
            text: qsTr("Settings")
            pix: Funcs.loadImage("settings.svg")
            onClicked: settings()
        }
        ToolItem{
            text: qsTr("About")
            pix: Funcs.loadImage("about.svg")
            onClicked: about()
        }
        ToolItem{
            text: qsTr("Exit")
            pix: Funcs.loadImage("exit.svg")
            onClicked: quit()
        }
    }
            Rectangle{
                id: _divider
                width: 1
                height: parent.height - 20
                color: palette.mid
                anchors{
                    left: _main_logo.right
                    leftMargin: 40
                    verticalCenter: parent.verticalCenter
                }
            }

            LogoImage {
                anchors{
                    left: parent.left
                    leftMargin: 20
                    verticalCenter: parent.verticalCenter
                }

                id: _main_logo
                height: parent.height - 20
                width: 150
            }

    background: Rectangle {
                 implicitHeight: Const.xemBtnHeight
                 color: palette.base

                 XemLine {
                     anchors.bottom: parent.bottom
                     blue: false
                 }
             }
}
