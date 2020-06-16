import QtQuick 2.12
import QtQuick.Controls 2.12


TextField{
    id: _base

    signal wheelUp()
    signal wheelDown()
    signal changed()

    rightPadding: 5
    leftPadding: 5
//    bottomInset: 5
    bottomPadding: 3
//    height: 30

    focus: true
    maximumLength: 40
    horizontalAlignment: TextInput.AlignLeft
    verticalAlignment: TextInput.AlignVCenter
    inputMethodHints:  Qt.ImhFormattedNumbersOnly

    validator : RegExpValidator { regExp : /([0-9]+\.)?[0-9]+/ }
    onTextEdited:{
        if(acceptableInput){
            _base.changed();
        }
    }

    font: simpleFont

    MouseArea{
        anchors.fill: parent
        propagateComposedEvents: true
        onClicked: {
            parent.forceActiveFocus();
        }
        onWheel: {
            if(wheel.angleDelta.y > 0){
                wheelUp()
            }else{
                wheelDown()
            }
        }
    }

    background: Rectangle{
        radius: 1
        color: palette.base
        height: parent.height
        XemLine{
            anchors{
                bottom: parent.bottom
            }
            width: parent.width
        }
    }
}
