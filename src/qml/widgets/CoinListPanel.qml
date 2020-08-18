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

        MyMenuItem{
            text: qsTr("Create a new address","Context menu item")
            onTriggered: {
                createAddress(_cxt_menu.index)
            }
        }
        MyMenuItem{
            text: qsTr("Add a watch only address","Context menu item")
            onTriggered: {
                addWatchAddress(_cxt_menu.index)
            }
        }

        Component.onCompleted:{
            if(CoinApi.debug){
                _cxt_menu.addItem(_update_coin);
                _cxt_menu.addItem(_clear_coin);
            }
        }
    }

    Item{

        MyMenuItem{
            id: _update_coin
            text: qsTr("Update","Debug context menu")
            onTriggered: {
                api.updateCoin(_cxt_menu.index)
            }
        }
        MyMenuItem{
            id: _clear_coin
            text: qsTr("Clear","Debug context menu")
            onTriggered: {
                api.clearCoin(_cxt_menu.index)
            }
        }
    }

    ListView{
        id: _coin_list
        currentIndex : -1
//        spacing: 10
        anchors{
            fill:parent
            topMargin: 10
            rightMargin: 10
        }
        clip: true

      ScrollBar.vertical: ScrollBar {
          id: _scroll
          parent: _coin_list.parent
          anchors.top: _coin_list.top
          anchors.left: _coin_list.right
          anchors.bottom: _coin_list.bottom
//          visible: true
          policy: ScrollBar.AsNeeded
          width: 10
          contentItem: Rectangle {
                    implicitWidth: 10
                    radius: width / 2
                    color: _scroll.pressed ? palette.mid: palette.midlight
                }
      }


        delegate:  CoinDelegate{
            // property variant modelData: model
            id: _coin_row
            name:   model.fullName
            icon:   Funcs.loadImage(model.icon)
            visible: model.visible
            amount:   CoinApi.settings.coinBalance( model.balance )
            unit:   CoinApi.settings.coinUnit( model.unit )
            fiatAmount:   model.fiatBalance
            fiatUnit:   api.currency
            test: model.test
            enabled: model.enabled
            selected: model.index === _coin_list.currentIndex
            addressModel: CoinApi.dummy ? api.getAddressModel(index): model.addressModel
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
