import QtQuick 2.12
//import QtGraphicalEffects 1.12
import "../js/constants.js" as Const


Base {
    id: _base

    property string txId: ""
    property string block: ""
    property string fee: ""

    property alias time: _header.time
    property alias from: _header.from
    property alias to: _header.to
    property alias sent: _header.sent
    property alias confirmCount: _header.confirmCount
    property alias amount: _header.amount
    property alias unit: _header.unit
    property alias fiatAmount: _header.fiatAmount
    property alias fiatUnit: _header.fiatUnit

    readonly property int infoHeight: 150
    antialiasing: true

    height: _header.height
    width: parent.width

    signal txClick();

    property bool expanded: false
    onExpandedChanged: {
        console.log(expanded)
        _base.state = expanded?"expanded":"collapsed"
        _animation_to.running = expanded
        _header.expanded = expanded
        _animation_back.running = !expanded
        if(expanded){
            _loader.setSource("TxDetailsPanel.qml",{
                                  "topOffset": _header.height - 10 ,
                                  "height"  : infoHeight,
                                  "txId"    : _base.txId,
                                  "block"    : _base.block,
                                  "fee"    : _base.fee,
                                  "confirmText" : _base.confirmCount,
                              })
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
        radius: 10

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
                anchors{
                    top: parent.top
                    horizontalCenter: parent.horizontalCenter
                }
                width: parent.width - 20
            }
        }
            TxRow{
                id: _header
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
