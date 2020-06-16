import QtQuick 2.12
import QtQuick.Controls 2.12
import "../api"

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

    onModelChanged: {
        console.log("address model changed " + coinUnit)
        // _list_view.forceLayout()
    }


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
        MenuItem{
            text: qsTr("Copy address")

            onTriggered: {
                copyAddress(_cxt_menu.index)
            }
        }

        MenuItem{
            text: qsTr("Show details ")

            onTriggered: {
                showAddressDetails(_cxt_menu.index)
            }
        }

        MenuItem{
            text: qsTr("Export transactions")

            onTriggered: {
                actionExportTransactions(_cxt_menu.index)
            }
        }
        MenuItem{
            text: qsTr("Update")

            onTriggered: {
                actionUpdateAddress(_cxt_menu.index)
            }
        }
        MenuItem{
            text: qsTr("Remove address")

            onTriggered: {
                removeAddress(_cxt_menu.index)
            }
        }

        MenuItem{
            text: qsTr("Clear transactions")

            onTriggered: {
                actionClearTransactions(_cxt_menu.index)
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
            name: modelData.name
            label: modelData.label
            amount: CoinApi.settings.coinBalance( modelData.balance )
            unit: coinUnit
            fiatUnit: api.currency
            fiatAmount: modelData.fiatBalance
            selected: _base.selected && model.index === _list_view.currentIndex

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
                _cxt_menu.open()
            }
        }

    }

}
