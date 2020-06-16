import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"

BasePage {

        id: _base
        readonly property int pageId: Constants.pageId.palette

        function makeModel(){
            var map = []
            for ( var i in _base.palette){
                console.log(`palette key: ${i}`)
                map.push({
                     name: i,
                     color: _base.palette[i],
                })
            }

            return map
        }

        TxButton{
            id: _btn_close
            anchors{
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                margins: defaultMargin
            }

            text: qsTr("Close")

            onClicked: {
                _base.popPage()
            }
        }

        Rectangle{
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                bottom: _btn_close.top
                margins: 10
            }
            radius: 10
            color: palette.base
            width: 500


            ListView{
            id: _list
            anchors{
                margins: 10
                top: parent.top
                left: parent.left
            }
            spacing: 3
            model: makeModel()
            height: parent.height - 40
            width: parent.width - 40
            clip: true
            delegate:
                Rectangle{
                    width: 500
                    height: 30
                    color: modelData.color
                    radius: 5
                    Label{
                        anchors{
                            fill: parent
                            margins: 100
                            topMargin: 0
                            bottomMargin: 0
                        }
                    id: _label
                    text: modelData.name + ": " + modelData.color
                    horizontalAlignment: 	Text.AlignHCenter
                    verticalAlignment: 		Text.AlignVCenter
                    font{
                        pixelSize: 16
                        bold: false
                    }
                    color: "black"
                    background: Rectangle{
                        color: "#90FFFFFF"
                        radius: 5
                        border{
                            width: 2
                            color: "black"
                        }
                    }
                    }
            }
        }
    }
}
