import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import "../api"
import "../controls"

import "../js/functions.js" as Funcs



Item {
    id: _base


    signal coinSelect(int index);
    signal addressSelect(int index)
    signal createAddress(int index)
    signal addWatchAddress(int index)

    antialiasing: true
    property alias model: _coin_list.model
    property variant openedItems: []

    function emitChange(expanded){
            if(expanded){
                _base.coinSelect( _coin_list.currentIndex );
            }else{
                //_base.coinSelect(-1)
            }
    }

    function closeList(){
        _coin_list.currentItem.expanded = false
    }

    Menu{
        id: _cxt_menu
        property int index: 0

        MenuItem{
            text: qsTr("Create new address")
            onTriggered: {
                createAddress(_cxt_menu.index)
            }
        }
        MenuItem{
            text: qsTr("Add watch only address")
            onTriggered: {
                addWatchAddress(_cxt_menu.index)
            }
        }

    }


    ListView{
        id: _coin_list
//        spacing: 10
        anchors{
            fill:parent
            topMargin: 10
        }


        delegate:  CoinDelegate{
            // property variant modelData: model
            id: _coin_row
            icon:   Funcs.loadImage(modelData.icon)
            name:   modelData.fullName
            visible: modelData.visible
            //amount: modelData.balanceHuman
            // unit:   modelData.unit
            amount:   CoinApi.settings.coinBalance( modelData.balance )
            unit:   CoinApi.settings.coinUnit( modelData )
            fiatAmount:   modelData.fiatBalance
            fiatUnit:   api.currency
            test: modelData.test
            enabled:    modelData.enabled
            selected: model.index === _coin_list.currentIndex
            addressModel: CoinApi.dummy ? api.getAddressModel(index):modelData.wallets
           // expanded: modelData.expanded
            onCoinClick: {
                // strict order !!!
                var addressCount = api.walletsCount(model.index)
                if (_coin_row.enabled){
                    _coin_list.currentIndex = model.index
                    _coin_row.expanded = !_coin_row.expanded
                    emitChange(_coin_row.expanded);
                }
            }
            onAddressClick: {
                _coin_list.currentIndex = model.index
                if( _coin_row.expanded ){
                    _base.addressSelect(index);
                }
            }
            onRightClick: {
                _cxt_menu.y = pty + _coin_list.y + _coin_row.y
                _cxt_menu.x = ptx + _coin_list.x + _coin_row.x
                _cxt_menu.index = model.index
                _cxt_menu.open()
            }
        }

        onCurrentIndexChanged: {
            emitChange(currentItem.expanded)
        }
    }
}
