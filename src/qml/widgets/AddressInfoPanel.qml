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
    property alias coinName: _coin_row.text
    property alias coinIcon: _coin_icon.source
    property alias amount: _crypto.amount
    property alias unit: _crypto.unit
    property alias fiatAmount: _fiat.amount
    property alias fiatUnit: _fiat.unit
    property alias isUpdating: _tx_list.isUpdating
    property bool readOnly: false
    property bool receiveOnly: false
    readonly property int icon_size: 45



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
        spacing: 20

        Base{

            height: 60
            anchors{
                left: parent.left
                right: parent.right
            }

            Image {
                id: _coin_icon
                anchors{
                    left: parent.left
                    top: parent.top
                    margins: 10
                    leftMargin: 30
                }
                sourceSize.height: icon_size
                sourceSize.width: icon_size
                source: Funcs.loadImage("btc_icon.png")
                height: icon_size
                width: icon_size
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
            LabelText{
                id: _coin_row
                anchors{
//                    top: parent.top
//                    horizontalCenter: parent.horizontalCenter
//                    horizontalCenterOffset: -20
                    verticalCenter: _coin_icon.verticalCenter
                    left: _coin_icon.right
                    leftMargin: 20
                    margins: 10
                }
            }
            XemLine{
                anchors{
                    bottom: parent.bottom
                    left: parent.left
                    right: parent.right
                    topMargin: 10
                    margins: 20
                    bottomMargin: 0
                }
                id: _coin_line
                blue: false
            }
        }


        MoneyCount{
            anchors{
                horizontalCenter: parent.horizontalCenter
            }
            id: _crypto
            color: palette.text
            unit: api.unit
            fontSize: 20
            amounFontSize: 30
            width: 200
        }

        MoneyCount{
            anchors{
                horizontalCenter: parent.horizontalCenter
            }
            id: _fiat
            color: palette.text
            unit: api.currency
            fontSize: 14
            amounFontSize: 20
            width: 200
        }



        Row{
            anchors{
                horizontalCenter: parent.horizontalCenter
            }

                spacing: 30


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

        TitleText{
            anchors{
                horizontalCenter: parent.horizontalCenter
            }
            id: _tx_label
            text: qsTr("Transactions history")
            sub: true
        }

        XemLine{
            anchors{
                left: parent.left
                right: parent.right
                rightMargin: 20
                leftMargin: 20
            }
            id: _tx_line
            blue: false
        }
        Row{
            anchors{
                horizontalCenter: parent.horizontalCenter
            }
            spacing: 50
            TxFilterBtn{
                text: qsTr("All")
                checked: true
                onSelect: {
                    api.txSortingOrder = 0
                }
            }
            TxFilterBtn{
                text: qsTr("Sent")
                onSelect: {
                    api.txSortingOrder = 1
                }
            }
            TxFilterBtn{
                text: qsTr("Received")
                notLast: false
                onSelect: {
                    api.txSortingOrder = 2
                }
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
