import QtQuick 2.12

BasePopup{
    id: _base
    ok: false
    canBeAccepted: false
    closable: false
    acceptText: qsTr("Accept (10)")
    rejectText: qsTr("Decline")
    onVisibleChanged:{
        if(visible){
            _activity_timer.running = true;
        }
    }
        Text{
            id: _message
            width: 500
            lineHeight : 2.
            anchors{
//                horizontalCenter: parent.horizontalCenter
                top:parent.top
                topMargin: 40
                left: parent.left
                leftMargin: 40

            }

            color: palette.text
            wrapMode: Text.Wrap
            antialiasing: true
            horizontalAlignment: Text.AlignLeft
            elide: Text.ElideRight
            text: qsTr("<b><font color=\"red\">IMPORTANT NOTE:</font></b> The current application version is an alpha-version and does not warrant stable operation or safety of your finances. Please use this version with precautions for information only, as it is designed for demonstration purposes only.")
            font{
                family: "Arial"
                pixelSize: 14
            }

        Timer{
            id: _activity_timer
            property int counter: 10
            interval: 1000
            onTriggered: {
                if(--counter  === 0 ){
                    _base.canBeAccepted = true
                    _base.acceptText = qsTr("Accept")
                }else{
                    running = true
                    _base.acceptText = qsTr("Accept (%1)").arg(_activity_timer.counter)
                }
            }
        }
        }
}

