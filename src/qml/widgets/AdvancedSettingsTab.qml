
import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../pages"

Tab {
    id: _base
    property alias useNewAddress: _use_new.checked
    property alias rateSourceModel: _rate_source.model
    property alias currentRateSourceIndex: _rate_source.index

    signal clearWallet();
    signal restoreWallet();
    signal selectRateSource(int index)



        Column{
            spacing: 10
            anchors{
                top: parent.top
                left: parent.left
                right: parent.right
            }
            SettingsFont{
                id: _font_dg
                width: parent.width

                name: qsTr("Application font:")
                visible: false
            }

            SettingsComboBox{
                id: _rate_source
                role: "name"
                name: qsTr("Rates source:")
                width: parent.width
                onSelect: selectRateSource(index)
                visible: false
            }
            SettingsComboBox{
                id: _zeros
                role: "name"
                name: qsTr("Zeros after point:")
                width: parent.width
                visible: false
            }


            SettingsCheckBox{
                id: _use_new
                name: qsTr("Always send change on new address")
                width: parent.width
                visible: false

                ToolTip.delay: 1000
                ToolTip.timeout: 5000
                ToolTip.visible: false
                ToolTip.text: qsTr("This increases your safity.")
            }
        }

        Column{
            id: _content
            spacing: 10
            anchors{
                bottom: parent.bottom
                left: parent.left
                right: parent.right
                margins: 20
            }
            TxBigButton{
                id: _btn_clear
                text: qsTr("Clear wallet")
                width: 300

                anchors{
                    horizontalCenter: parent.horizontalCenter
                }

                onClicked: {
                    _reset_warning.accept.connect(function(){
                    clearWallet()
                    close()
                    })

                    _reset_warning.open()
                }
                MsgPopup{
                    id: _reset_warning
                    visible: false
                    ok: false
                    text: qsTr("You are about destroy all you keys and there is a risk to lose money! Make sure you have backup copy. Continue?")
                }
            }
            TxBigButton{
                id: _btn_restore
                text: qsTr("Restore wallet")
                width: 300
                // visible: false

                anchors{
                    horizontalCenter: parent.horizontalCenter
                }

                onClicked: {
                    _reset_warning.accept.connect(function(){
                        _reset_warning.close()
                        restoreWallet()
                    })

                    _reset_warning.open()
                }
            }
        }

}
