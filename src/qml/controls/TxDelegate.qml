import QtQuick 2.12
import "../api"
import "../js/constants.js" as Const
import "../js/functions.js" as Funcs

/*

            from: 	modelData.fromAddress
            to: 	modelData.toAddress
            amount: CoinApi.settings.coinBalance(modelData.balance)
            unit: CoinApi.settings.coinUnit(null)
            fiatAmount: modelData.fiatBalance
            fiatUnit: api.currency
            time: modelData.timeHuman
            txId: modelData.name
            block: modelData.block
            fee: modelData.feeHuman
            confirmCount: modelData.confirmCount
            status: modelData.status
  */

Base {
    id: _base
    property variant tx: null
    readonly property int infoHeight: 140
    antialiasing: true

    height: _header.height
    width: parent.width

    signal txClick();

    property bool expanded: false
    onExpandedChanged: {
        _base.state = expanded?"expanded":"collapsed"
        _animation_to.running = expanded
        _header.expanded = expanded
        _animation_back.running = !expanded
        if(expanded){
            var opts =  {
                                  "block" : tx.block,
                                  "fee" : tx.feeHuman,
                                  "hash" : tx.name,
                              };
            if(CoinApi.dummy){
                opts["inputsModel"] = CoinApi.coins.inputsModel;
                opts["outputsModel"] = CoinApi.coins.outputsModel;
            }else{
                opts["inputsModel"] = tx.inputsModel;
                opts["outputsModel"] = tx.outputsModel;
            }
            // console.log(`opts: ${opts}`)
            // Funcs.explore( opts , "tx opts" )
            _loader.setSource("TxDetailsPanel.qml", opts);
        }else{
            _loader.setSource("EmptyTxInfo.qml")
        }
    }

/*
    Binding{
        target: _loader.item
        property: "confirmText"
        value: _base.confirmCount
        // when: loader.status == Loader.Ready && expanded
    }
    */

    function updateConfirm(value){
        _base.confirmCount = value;
        if(_loader.item && expanded){
            _loader.item.confirmText = value;
        }
    }

    Rectangle{
        id: _border

        /*
        border{
            color: palette.text
            width: 1
        }
        */
//        radius: 10

        color: palette.base

        anchors{
            fill: parent
            leftMargin: 5
            rightMargin: 5
        }


        Loader{
            id: _loader
            anchors{
                top: parent.top
                topMargin: 5
                left: parent.left
                right: parent.right
            }
            height: contentChildren.height

            XemLine{
                id: _top_line
                visible: false
                anchors{
                    top: parent.top
                    horizontalCenter: parent.horizontalCenter
                }
                width: parent.width - 20
            }
        }
            TxRow{
                id: _header

//                hash: tx.index + '. ' + tx.name
                time: tx.timeHuman
                amount: CoinApi.settings.coinBalance( model.balance )
                // unit: CoinApi.settings.coinUnit( null )
                unit: CoinApi.coins.unit
                fiatAmount: tx.fiatBalance
                fiatUnit: api.currency
                confirm: tx.confirmCount
                status: tx.status

                anchors{
                    top: parent.top
                    left: parent.left
                    right: parent.right
                }
                MouseArea{
                    anchors.fill: parent
                    onClicked: {
                        txClick()
                    }
                }
            }
    }
    /*
    InnerShadow {
            id: _shadow
            anchors.fill: _border
            cached: true
            horizontalOffset: -5
            verticalOffset: -5
            radius: 8.0
            samples: 16
            color: palette.buttonText
            smooth: true
            source: _border
        }
        */




    NumberAnimation {
        id: _animation_to
        target: _base
        property: "height"
        duration: 200
        from: _header.height
        to: infoHeight
        easing.type: Easing.InOutQuad
    }

    NumberAnimation {
        id: _animation_back
        target: _base
        property: "height"
        duration: 200
        from: infoHeight
        to: _header.height
        easing.type: Easing.InOutQuad
    }
    state: "collapsed"
    states: [
        State {
            name: "collapsed"
        },
        State {
            name: "expanded"
        }
    ]
}
