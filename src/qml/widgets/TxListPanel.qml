import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/functions.js" as Funcs



Rectangle {
    id: _base
    property alias model: _list.model
    property bool isUpdating
    color: "transparent"
    radius: 10
    border.width: 2
    border.color: "#80FFFFFF"




    ListView{
        id: _list
        anchors.fill: parent
        spacing: 6
        clip: true

        /*
        header: Rectangle{
            color: "green"
            height: 10
            width: _list.width
        }
        */
        footer: TxListFooter{
            visible: _base.isUpdating
        }

        delegate: TxDelegate{
            id: _me
            width: _tx_list.width

            from: 	modelData.fromAddress
            to: 	modelData.toAddress
            /*
            amount: modelData.balanceHuman
            unit: api.unit
            */
            amount: CoinApi.settings.coinBalance( modelData.balance )
            unit: CoinApi.settings.coinUnit( null )
            fiatAmount: modelData.fiatBalance
            fiatUnit: api.currency
            time: modelData.timeHuman
            sent: modelData.sent
            txId: modelData.name
            block: modelData.block
            fee: modelData.feeHuman
            confirmCount: modelData.confirmCount

/*
            Binding{
                target: _me
                value: modelData.confirmCount
                property:"confirmCount"

            }
            */



            // onConfirmCountChanged: {
            //     console.log(`new confirm ${confirmCount}`)
            // }

            onTxClick:{
                expanded = !expanded
            }
        }
    }


            Connections{
                /*
                property binding doesnt work in modelData

                TODO: make it straight
                 */
                target: CoinApi.coins.coin
                onHeightChanged:{
                    var item = null;
                    for(var i = 0; i < _list.count; ++i){
                        item = _list.itemAtIndex(i);
                        if(item){
                            // console.log(`================!!!!!!!! ${_list.model[i].confirmCount}`)
                            item.updateConfirm(_list.model[i].confirmCount);
                            print(item.confirmCount)
                        }
                    }
                }
            }
}
