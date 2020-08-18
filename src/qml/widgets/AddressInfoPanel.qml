import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/functions.js" as Funcs
import "../js/constants.js" as Const


Base {
    id: _base

    readonly property QtObject api: CoinApi.coins
    property alias coinName: _top_panel.coinName
    property alias coinIcon: _top_panel.coinIcon
    property alias amount: _top_panel.amount
    property alias fiatAmount: _top_panel.fiatAmount
    property alias label: _label.text
    property alias message: _message.text
    property alias isUpdating: _tx_list.isUpdating
    property bool readOnly: false
    property bool receiveOnly: false

    property int totalTxNumber: 0
    property int existingTxNumber: 0



    signal sendMoney()
    signal receiveMoney()
    signal exchangeMoney()

    Column{
        id: _info_panel
        anchors{
            top: 	parent.top
            left:	parent.left
            leftMargin: 20
            right: 	parent.right
            rightMargin: 20

        }
        spacing: 10
       TopAddressPanel{
           id: _top_panel
           height: 60
       }


        TitleText{
            id: _label
            anchors{
                        horizontalCenter: parent.horizontalCenter
            }
            font{
                pixelSize: 16
            }
        }
        XemLine{
            anchors{
                        horizontalCenter: parent.horizontalCenter
            }
            width: parent.width * .5
            blue: false
            visible: _label.text.length > 0
        }
        LabelText{
            id: _message
            font{
                pixelSize: 12
                bold: false
            }
        }
        XemLine{
            anchors{
                        horizontalCenter: parent.horizontalCenter
            }
            width: parent.width * .5
            blue: false
            visible: _message.text.length > 0
        }



        Row{
            anchors{
                horizontalCenter: parent.horizontalCenter
//                left: parent.left
//                right: parent.right
            }

                spacing: (parent.width - minWidth *.5) * .1 + 10


                TxBigButton{
                    id: _send_btn
                    text: qsTr("Send","Main page")
                    enabled: !_base.readOnly && !_base.receiveOnly
                    onClicked: {
                        sendMoney();
                    }
                }
                TxBigButton{
                    id: _receive_btn
                    text: qsTr("Receive","Main page")
                    enabled: !_base.readOnly
                    onClicked: {
                        receiveMoney();
                    }
                }
                TxBigButton{
                    text: qsTr("Exchange","Main page")
                    enabled: false
                    onClicked: {
                        exchangeMoney()
                    }
                }
            }

        Base{
            id: _tx_header
            height: 30
            anchors{
                left: parent.left
                right: parent.right
                margins: 20
            }

        TitleText{
            anchors{
                centerIn: parent
            }
            id: _tx_label
            text: qsTr("Transactions history")
//            font{ pixelSize: 14 }
            sub: true
        }
        LabelText{
            anchors{
//            right: parent.right
                    verticalCenter: _tx_label.verticalCenter
                    left: _tx_label.right
                    leftMargin: 20
            }
            text: qsTr("%1 / %2").arg(existingTxNumber).arg(totalTxNumber)
        }

        }

    }

    TxListPanel{
        id: _tx_list
        anchors{
            top: _info_panel.bottom
            bottom: parent.bottom
            left:	parent.left
            right: 	parent.right
            topMargin: 20
        }

        model: api.txModel
    }



}
