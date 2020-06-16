import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"

BasePopup {
    id: _base

    ok: true

    property alias txHash: _tx_hash.text
    property string coinName : ""

    Column{
        id: _column

        anchors{
//            fill: parent
//            centerIn: parent
            verticalCenter: parent.verticalCenter
            left: parent.left
            right: parent.right
            margins: 20
        }

        spacing: 30

        Text{
            text: qsTr("Your transaction has sent succefully. Here is the transaction ID")
            font: simpleFont
            color: palette.mid
        }

        TextField{
            id: _tx_hash
            font{
                pixelSize: 12
                family: "Arial"
                bold: true
            }
            color: palette.highlightedText
            background: Rectangle{
                color: palette.highlight
            }

            selectionColor: palette.base
            selectedTextColor: palette.text
            selectByMouse: true
            readOnly: true

            anchors{
                left: parent.left
            }


            ToolButton{
                id: _copy_btn
                height: parent.height

                width: 50
                anchors{
                    verticalCenter: parent.verticalCenter
                    left: parent.right
                    margins: 10
                }
                text: qsTr("Copy")
                font{
                    pixelSize: 10
                }
                onClicked:{
                    CoinApi.ui.copyToClipboard( txHash )
                }
                background: Rectangle{
                    color: {

                            if( _copy_btn.pressed){
                                return palette.button
                            }
                            else if(_copy_btn.hovered){
                                return palette.alternateBase
                            }
                            return palette.highlight
                    }
                }
            }
        }

        Text {
            text: qsTr("You can track confirmation progress <a href='#'>here<a\>.")

            onLinkActivated: {
                // don't need args
                if (coinName.length > 0){
                    var final_url = "";
                    if ( coinName === "ltc"){
                        final_url = qsTr("https://ltc.btc.com/%1").arg(txHash);
                    }else{
                        // btc
                        final_url = qsTr("https://www.blockchain.com/en/%1/tx/%2").arg(coinName).arg(txHash);
                    }
                    const browse_result = Qt.openUrlExternally(final_url);
                    console.log(`open TX url '${final_url}' => ${browse_result}`);
                }
            }
            font: simpleFont
            color: palette.mid
        }
    }



}
