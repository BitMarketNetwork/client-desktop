import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"


Base {
    color: palette.base
    renderColor: "blue"
    property alias model: _list.model


    XemLine{
        blue: false
        width: parent.width * 0.5
        anchors{
            top: parent.top
            horizontalCenter: parent.horizontalCenter
        }
        opacity: 0.5
    }

    ListView{
        id: _list
        anchors{
            fill: parent
            margins: 5
        }
        clip: true
        spacing: 1
        delegate: Base{
            id: _cell
            width: 300
            height: 15
            MouseArea{
                id: _mouse
                anchors{
                    fill: parent
                }
                hoverEnabled: true
                onDoubleClicked: {
                    console.log(modelData.addressName)
                    CoinApi.ui.copyToClipboard( modelData.addressName)
                }
            }
            Row{
                anchors{
                    fill: parent
                }
                Label{
                    text: qsTr("%1.").arg(model.index + 1)
                    width: 17
                    height: parent.height
                    color: palette.text
                    font{
                       pixelSize: 10
                    }
                }
                Label{
                    id: _address
                    text: modelData.addressName
                    width: 270
                    font{
                       pixelSize: 10
                    }
                    color: _mouse.containsMouse? palette.highlight: palette.text
                }
                MoneyCount{
                    amount: modelData.amountHuman
//                    unit: CoinApi.coins.unit
                    unit: ""
                    fontSize: 10
                    width: 100
                    color: _mouse.containsMouse? palette.highlight: palette.text
                }
            }
        }
    }
}
