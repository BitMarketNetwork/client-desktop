
import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/constants.js" as Constants
import "../js/functions.js" as Funcs

import Bmn 1.0



NewTxPage {
    id: _base
    action: qsTr("Send a transaction")
    actionIcon: Funcs.loadImage("send.svg")
    valid: false
    readonly property int pageId: Constants.pageId.send


    onAccept: {
        var result = _tx_controller.prepareSend();
        if(result){
            _approve_popup.visible = true;
        }
    }

    onCancel: {
        _tx_controller.cancel()
    }

    Component.onCompleted:{
//            _base.wait(2000)
    }

//    Flickable{
        Rectangle{
        width: parent.width
//        ScrollBar.vertical: ScrollBar{
//            width: 30
//            policy: ScrollBar.AlwaysOn
//        }
//        clip: true
//        contentHeight: 600
        height: 600
        y: 150
        anchors{
            top: parent.top
//            bottom: parent.bottom
//            topMargin: 150
        }

    Column{
        id: _main_column
        anchors{
            fill: parent
//            topMargin: 150
        }
        spacing: 20
        /*
            logic area
        */

        TxController{
            id: _tx_controller

            onFail: {
                console.error(error)
                msgbox(error);
            }

            onSent: {

                /*
                var msg = msgbox(qsTr("Transaction has sent"))
                msg.reject.connect(function(){
                    popPage();
                });
                */
                _result_popup.txHash = txHash
                _result_popup.open()

            }

            onCanSendChanged:{
                console.log(`Can send:`, canSend)
                _base.valid = _tx_controller.canSend
            }
            function less(){}
            function more(){}
        }

        Item {
            visible: false
            SendApprovePopup{
                id: _approve_popup

                amount: _tx_controller.amount
                fee: 	_tx_controller.feeAmount
                change: _tx_controller.changeAmount
                changeAddress: _tx_controller.changeAddress
                target: _tx_controller.receiverAddress
                unit: 	CoinApi.coins.unit

                onSend: {
                    _tx_controller.send()
                }
            }
            TxResultPopup{
                id: _result_popup
                // coinName: _base.coinName
                coinName: api.coin.shortName
                onReject: {
                    popPage()
                }
            }
        }

        /**/


        /*
          // ew dont need from addres cause we gather UTXO from different tx
        TxAddressInput{
            anchors{
                left: parent.left
                right: parent.right
            }
            id: _from_address
            text: qsTr("From:")
            address: api.address.name
            readOnly: true
        }
        */
        AdddressWidget{
            id: _to_address
            valid: _tx_controller.receiverValid
            onChanged: {
                _tx_controller.receiverAddress = address
            }

//            addressList: _tx_controller.targetList
        }
        AmountWidget{
            id: _amount
            /*
                logic
            */
            amount: _tx_controller.amount
            fiatAmount: _tx_controller.fiatAmount
            maximum: _tx_controller.maxAmount
            onMax: _tx_controller.setMax()
            onEdit: {
                    _tx_controller.amount = value
                }
            onLess:{
                _tx_controller.less();
            }
            onMore:{
                _tx_controller.more()
            }
            maxLength: 16
            valid: ! _tx_controller.wrongAmount
        }

        TxSourceWidget{
            id: _source

            allAmount: _tx_controller.maxAmount
            allFiat: _tx_controller.fiatBalance
            sourceModel: _tx_controller.sourceModel
            useAllAmount: _tx_controller.useCoinBalance
            onRecalcSources: {
                _tx_controller.recalcSources()
            }

            onUseAll: {
                _tx_controller.useCoinBalance = on
            }
        }
        FeeWidget{
            id: _fee

            /*
                logic
            */
            amount: _tx_controller.spbAmount
            onSlider: {
                _tx_controller.spbFactor = value
            }
            onInput: {
                _tx_controller.spbAmount = value
            }

            sliderValue: _tx_controller.spbFactor
            //blocksCount: qsTr("Target within %1 blocks").arg(_tx_controller.targetBlocks)
            confirmTime: _tx_controller.confirmTime

            substractFee: _tx_controller.substractFee
            onSubstractFeeChanged: {
                _tx_controller.substractFee = substractFee;
            }



        }

        ChangeWidget{
            id: _change
            leftOverAmount: _tx_controller.changeAmount
            newAddressLeft: _tx_controller.newAddressForChange
            onNewAddressLeftChanged: {
                _tx_controller.newAddressForChange = newAddressLeft
            }
        }
    }

/*
        SourceAddressesWidget{
            id: _money_source
            anchors{
                left: parent.left
                right: parent.right
            }
            model: api.addressModel

        }

        LeftoverWidget{
            id: _left_over
            anchors{
                left: parent.left
                right: parent.right
            }

            newAddress: _tx_controller.newAddressForChange
            onNewAddressChanged: {
                console.log(newAddress)
                _tx_controller.newAddressForChange = newAddress
            }
        }
        */


    }

}
