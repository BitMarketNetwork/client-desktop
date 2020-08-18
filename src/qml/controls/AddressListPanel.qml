import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"
import "../widgets"

Base {
    id: _base
    property bool selected: false
    property variant coinUnit: null
    property alias model: _list_view.model
    readonly property int topmargin: 80
    anchors{

        left: parent.left
        right: parent.right
        top: parent.top
       // margins: 5
    }

    //border.color: palette.buttonText
    //border.width: 2
    antialiasing: true


    height: _list_view.count * 40 + topmargin + 10

    signal addressClick(int index);

    onHeightChanged:{
        console.log(`loader height: ${height}`)
    }
    onModelChanged: {
        console.log("address model changed " + coinUnit)
        // _list_view.forceLayout()
    }

    function updateList() {
        // _list_view.forceLayout()
    }

    // Connections{
    //     target: addressModel
    //     onFilterUpdated:{
    //         console.log(`${model.emptyFilter} ${model.rowCount()} . ${height}`)
    //         updateList()
    //     }
    // }


    onSelectedChanged: {
        if(selected){
            //_list_view.currentIndex = 0
        }
    }

    Component.onCompleted:{
        console.debug("Address count:" , _list_view.count)
    }

    Menu{
        id: _cxt_menu
        property int index: 0
        property bool addressUpdating: false

        MyMenuItem{
            text: qsTr("Copy address","Context menu item")

            onTriggered: {
                copyAddress(_cxt_menu.index)
            }
        }

        MyMenuItem{
            text: qsTr("Show details ","Context menu item")

            onTriggered: {
                showAddressDetails(_cxt_menu.index)
            }
        }

        MyMenuItem{
            text: qsTr("Export transactions","Context menu item")

            onTriggered: {
                actionExportTransactions(_cxt_menu.index)
            }
        }
        MyMenuItem{
            text: qsTr("Update","Context menu item")
            enabled: !_cxt_menu.addressUpdating

            onTriggered: {
                actionUpdateAddress(_cxt_menu.index)
            }
        }
        MyMenuItem{
            text: qsTr("Remove address","Context menu item")
            enabled: !_cxt_menu.addressUpdating

            onTriggered: {
                removeAddress(_cxt_menu.index)
            }
        }
        
        Component.onCompleted:{
            if(CoinApi.debug){
                _cxt_menu.addItem(_clear_txs)
                _cxt_menu.addMenu(_balance_menu)
            }
        }
    }

    MyMenuItem{
        id: _clear_txs
        text: qsTr("Clear transactions","Context menu item")
        enabled: !_cxt_menu.addressUpdating

        onTriggered: {
            actionClearTransactions(_cxt_menu.index)
        }
    }
        MyMenu{
            id: _balance_menu
            title: qsTr("Balance manipulation")
            MyMenuItem{
                text: qsTr("Increase balance")
                onTriggered: {
                    CoinApi.coins.increaseBalance(_cxt_menu.index)
                }
            }
            MyMenuItem{
                text: qsTr("Reduce balance")
                onTriggered: {
                    CoinApi.coins.reduceBalance(_cxt_menu.index)
                }
            }
            MyMenuItem{
                text: qsTr("Clear balance")
                onTriggered: {
                    CoinApi.coins.clearBalance(_cxt_menu.index)
                }
            }
        }

    ListView{
        id: _list_view
        anchors.fill: parent
        anchors.topMargin: topmargin
        clip: true

        delegate: AddressRow{
            id: _row
            name: model.name
            label: model.label
            amount: CoinApi.settings.coinBalance( model.balance )
            unit: coinUnit
            fiatUnit: api.currency
            fiatAmount: model.fiatBalance
            selected: _base.selected && model.index === _list_view.currentIndex
            watchOnly: model.readOnly
            updating: model.isUpdating

            onClick: {
                if(_row.enabled){
                    _list_view.currentIndex = model.index
                    addressClick(model.index)
                }
                //console.log(`${model.index} => ${_list_view.currentIndex}`)
            }

            onRightClick: {
                _cxt_menu.y = pty + _list_view.y
                _cxt_menu.x = ptx + _list_view.x
                _cxt_menu.index = model.index
                _cxt_menu.addressUpdating = model.isUpdating
                _cxt_menu.open()
            }
        }

    }

}
