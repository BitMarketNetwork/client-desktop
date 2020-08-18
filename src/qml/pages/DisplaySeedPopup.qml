import QtQuick 2.12
import "../controls"
import "../api"
import "../pages"

BasePopup {
    id: _base
    title: qsTr("Seed phrase")
    Column{
        spacing: 10
        anchors{
            fill: parent
            margins: 10
        }
        DetailInput {
            id: _psw
            passwordInput: true
            name: qsTr("Password:")
            anchors{
                left: parent.left
                right: parent.right
            }
            height: 50
            labelWidth: 150
        }
        TxButton{
            id: _btn
            text: qsTr("Reveal seed phrase ")
            onClicked: {
                _seed.value = CoinApi.keyMan.revealSeedPhrase( _psw.value )
                _hide_timer.running = true
            }
            anchors{
                left: parent.left
                right: parent.right
            }
            enabled: _psw.value.length > 5 && CoinApi.keyMan.validatePasswordStrength(_psw.value) > 3
        }

        LongInput{
            id: _seed
            readOnly: true
            anchors{
                left: parent.left
                right: parent.right
             }
            height: 300

        }

        Timer{
            id: _hide_timer
            interval: 10000
            onTriggered: {
                _psw.value = ""
                _seed.value = ""
                _hide_timer.running = false
            }
        }

    }


    Component.onCompleted: {
    }
}
