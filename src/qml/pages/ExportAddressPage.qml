import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"

BasePage {
    property alias address: _name.value
    property alias label: _label.value
    property alias message: _message.value
    property alias created: _created.value
    property alias wif: _wif.value
    property alias pub: _pub.value

    signal closed()


        InfoLabel{
            anchors{
                top: parent.top
                horizontalCenter: parent.horizontalCenter
                margins: 30
            }
            text: qsTr("Address details")
            font{
                pixelSize: 24
                bold: true
            }
            color: palette.dark
        }
            TxButton{
            anchors{
                bottom: parent.bottom
                horizontalCenter: parent.horizontalCenter
                margins: 30
            }
                text: qsTr("Close")
                width: 150
                height: 50
                fontSize: 16
                onClicked: {
                    popPage()
                    closed()
                }
            }

    Rectangle{
        anchors{
            fill: parent
            margins: 20
            topMargin: 100
            bottomMargin: 100
        }

        focus: true

        color: palette.base


        Column{
            anchors{
                fill: parent
                margins: 20
            }
            spacing: 10

            DetailLabel{
                id: _name
                name: qsTr("Address:")
            }
            DetailLabel{
                id: _created
                name: qsTr("Created:")
            }
            DetailLabel{
                id: _pub
                name: qsTr("Public key (hex):")
            }
            DetailLabel{
                id: _wif
                name: qsTr("Private key (WIF):")
                echoMode: TextInput.Password
            }
            DetailInput{
                id: _label
                name: qsTr("Label:")
                width: parent.width
                height: 40
                maxLength: 54
                labelWidth: 200
            }
            LongInput{
                id: _message
                name: qsTr("Message:")
                height: 150
                width: parent.width
                labelWidth: 200
//                width: parent.width
            }
        }
    }

}
