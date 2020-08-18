import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/constants.js" as Constants
import "../js/functions.js" as Funcs
 Base{
    id: _base
    property alias confirm: _left.confirm
//    property alias hash: _tx_id.text
    property alias time: _left.time
    property alias amount: _right.amount
    property alias unit: _right.unit
    property alias fiatAmount: _right.amount
    property alias fiatUnit: _right.unit
    property bool expanded: false
    property int status: 3 // let it be last

    //
    property bool sent: false
    property int confirmCount: 0

    height: 40
    antialiasing: true


    readonly property int rightWidth: 140
    readonly property variant statusTexts: [
        // Pending, Unconfirmed, Confirmed, Complete
        qsTr("Pending","transaction status"),
        qsTr("Unconfirmed","transaction status"),
        qsTr("Confirmed","transaction status"),
        qsTr("Complete","transaction status"),
    ]
    readonly property variant statusIcons: [
        "clock.png",
        "sand_clock.png",
        "arrow_sent.png",
        "arrow_rcv.png",
    ]
    readonly property variant statusColors: [
        "#690027",
        "#d34e00",
        "#270069",
        "#276900",
    ]


   Base{
        id: _rect

//        color: palette.base

//        radius: 10
//        antialiasing: true
//        clip: true

        anchors{
            fill: parent
            margins: 1
            topMargin: 0
        }
        /*
        Rectangle{
            id: _top_header
//            color: palette.midlight
            height: 18
            radius: 2
            anchors{
//                bottom: parent.bottom
                top: parent.top
                left: parent.left
                right: parent.right
            }
            Text {
                id: _tx_id
                anchors{
                    fill: parent
                }
                font{
                    pixelSize: 12
                    family: "Arial"
                }
//                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                leftPadding: 18
                elide: Text.ElideRight
            }
        }
        */
        XemLine{
            width: parent.width * 0.5
            anchors{
//                bottom: _top_header.bottom
                horizontalCenter: parent.horizontalCenter
            }
            blue: false
            opacity: 0.5
            visible: false
        }
        XemLine{
            width: parent.width
            anchors{
                top: parent.top
            }
            blue: true
        }

        TxRowWidgetLeft{
            id: _left
            anchors{
                left: parent.left
                leftMargin: 13
                top: parent.top
//                bottom: _top_header.top
//                top: wop_header.bottom
                bottom: parent.bottom
                margins: 2

            }

        }
        TxRowWidgetRight{
            id: _right
            height: parent.height
            width: 150
            anchors{
                right: parent.right
//                top: _top_header.bottom
                top: parent.top
                bottom: parent.bottom
//                top: parent.top
//                bottom: _top_header.top
                margins: 1
            }
            statusText: statusTexts[status]
            statusColor: statusColors[status]


        }

        MouseArea{
            anchors.fill: parent
            onClicked: {
                console.log(model.name);
            }
        }
    }
        XemLine{
            id: _line
            blue: true
            width: parent.width
            visible: false

            anchors{
                top: parent.top
//                right: parent.right
//                right: parent.horizontalCenter
//                left: parent.left
                horizontalCenter: parent.horizontalCenter
                // leftMargin: 10
//                rightMargin: 0
                // topMargin: _base.topOffset
            }
     }
 }
