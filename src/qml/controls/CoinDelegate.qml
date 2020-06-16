import QtQuick 2.12
//import QtGraphicalEffects 1.12
import "../controls"
import "../js/constants.js" as Const

Item {
    id: _base

    property alias name: _header.name
    property alias icon: _header.icon
    property alias amount: _header.amount
    property alias unit: _header.unit
    property alias fiatAmount: _header.fiatAmount
    property alias fiatUnit: _header.fiatUnit
    property variant addressModel: null
    property alias test: _header.test


    height: _header.height
    width: parent.width
    antialiasing: true

    /*
      we can many expanded and not expanded items and only one selected !!!
    */
    property bool selected: false
    property bool expanded: false

    onSelectedChanged: {
        if(expanded && _base.enabled ){
            _loader.item.selected = _base.selected
        }
    }

    onAddressModelChanged: {
        // console.log(`new address model`)
        if( undefined == addressModel ){
            addressModel = [] // recursion
            return
        }
        else if(addressModel.length === 0){
            return
        }
        reload()
    }

    function reload() {
        // onChange()
        Qt.callLater(onChange)
    }

    Component{
        id: _full_list
        AddressListPanel {
            id: _full_list_impl
            model: addressModel
            coinUnit: unit
            onAddressClick: {
                if(_base.enabled){
                    _base.addressClick(index)
                }
            }
        }
    }

    Component{
        id: _empty_list
        EmptyAddressList {
            id: _empty_list_impl
        }
    }

    function onChange(){

        if(expanded){
            // console.error(`!!! ${name} !!!`)
            // console.trace()

            _loader.sourceComponent = _full_list
            if(_loader.item){
                _loader.item.selected = _base.selected
            }
        }else{
            _loader.sourceComponent = _empty_list

        }

        _animation_to.running = expanded
        _animation_back.running = !expanded
    }

    onExpandedChanged: {


        onChange()
    }


    signal coinClick()
    signal addressClick(int index)
    signal rightClick(int ptx, int pty)


    Rectangle{
        id: _rect
        color: _base.selected? palette.linkVisited : palette.base
        radius: 1
        visible: _base.visible

        border{
            width: _base.selected?1:0
            color: palette.link
        }

        anchors{
            fill: parent
            leftMargin: 5
            rightMargin: 5
        }

        Loader{
            id: _loader
            height: contentChildren.height
            enabled: _base.visible
            anchors{
                top: parent.top
                left: parent.left
                right: parent.right
            }
        }

    XemLine{
        id: _top_line
        anchors{
            top: parent.top
            topMargin: -1
            horizontalCenter: parent.horizontalCenter
        }
        width: parent.width - 20
        visible: !_base.selected
    }

        CoinRow{
            id: _header
            enabled: _base.enabled
            anchors{
                top: parent.top
                left: parent.left
                right: parent.right
            }
            MouseArea{
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                anchors.fill: parent
                onClicked: {
                    if (mouse.button === Qt.RightButton) {
                        _base.rightClick( mouse.x + _header.x , mouse.y + _header.y );
                    }
                    else{
                        _base.coinClick()
                    }
                }
            }
        }

    }

    NumberAnimation {
        id: _animation_to
        target: _base
        property: "height"
        duration: 200
        from: _header.height
        to: _loader.height
        easing.type: Easing.InOutQuad
    }

    NumberAnimation {
        id: _animation_back
        target: _base
        property: "height"
        duration: 200
        from: _base.height
        to: _header.height
        easing.type: Easing.InOutQuad
    }

    /*
    Connections{
        id: _address_connection
        target: _loader.item
        enabled: _base.expanded
        onAddressClick: {
            if(_base.enabled){
                _base.addressClick(index)
            }
        }
    }
        */


}
