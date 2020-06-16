import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"


SendWidget {
    id: _base
    title: qsTr("Send to:")
    height: 70
    titleColor: valid?palette.text: palette.brightText

    property alias address: _address_input.currentText
    property bool  valid: false
//    property alias addressList: _address_input.model

    signal changed()

    /*
        AddressComboBox{
            id: _address_input
            anchors{
                right: parent.right
                margins: defMargin
                left: parent.left
                leftMargin: defLeftMargin
                verticalCenter: parent.verticalCenter
            }

            focus: true
            inputMethodHints: Qt.ImhPreferUppercase
            padding: 5
            editable: true
            onAccepted:{
                changed()
            }

        }
        */
        TextField{
            id: _address_input
            property alias currentText: _address_input.text
            anchors{
                right: parent.right
                margins: defMargin
                left: parent.left
                leftMargin: defLeftMargin
                verticalCenter: parent.verticalCenter
            }

            focus: true
            inputMethodHints: Qt.ImhPreferUppercase

            padding: 5
            color: valid ? palette.mid: palette.brightText
//            editable: true
            onTextChanged:{
                changed()
            }

            background: Rectangle{
                color: palette.base
                XemLine{
                    anchors{
                        top: parent.top
                    }
                    width: parent.width
                    red: !valid
                    visible: false
                }
                XemLine{
                    anchors{
                        bottom: parent.bottom
                    }

                    width: parent.width
                    red: !valid
                }
            }
        }
}
