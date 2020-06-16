import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/constants.js" as Constants
import "../js/functions.js" as Funcs
 Base{
    id: _base
    property alias from: _left.from
    property alias to: _left.to
    property alias time: _left.time
    property alias amount: _right.amount
    property alias unit: _right.unit
    property alias fiatAmount: _right.amount
    property alias fiatUnit: _right.unit
    property bool expanded: false
    property string color: colors[status]

    //
    property bool sent: false
    property int confirmCount: 0

    height: 75
    antialiasing: true

    readonly property int status: {
            if(confirmCount > 0){
                return 1;
            }
            return 0;
    }
    readonly property variant colors: [
        Constants.txNotConfirmedColor,
        Constants.txInProcessColor,
        Constants.txSentColor,
        Constants.txReceivedColor
    ]
    readonly property variant statusTexts: [
        qsTr("Waiting"),
//        qsTr("In progress %1 form %2").arg(confirmCount).arg(confirmPlan),
        qsTr("In progress"),
        qsTr("Sent"),
        qsTr("Received"),
    ]
    readonly property variant statusIcons: [
        "clock.png",
        "sand_clock.png",
        "arrow_sent.png",
        "arrow_rcv.png",
    ]

    readonly property int rightWidth: 140


    Rectangle{
        id: _rect

        color: palette.base

        radius: 10
        antialiasing: true
        clip: true

        anchors{
            fill: parent
            margins: 5
        }

        TxRowWidgetLeft{
            id: _left
            height: parent.height
            anchors{
                left: parent.left
                leftMargin: 13
                top: parent.top
            }
        }
        TxRowWidgetRight{
            id: _right
            height: parent.height
            width: 150
            anchors{
                right: parent.right
                top: parent.top
                bottom: parent.bottom
            }
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
