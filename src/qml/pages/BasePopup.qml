import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"

/*
  we could use Dialog here but Popup is more versatile
*/

Popup{
    id: _base
    property alias ok: _btn_ok.visible
    property alias acceptText: _btn_accept.text
    property alias rejectText: _btn_reject.text
    property alias title: _title.text
    //property alias bgColor: _content.color
    property alias canBeClosed: _btn_ok.enabled
    property alias canBeAccepted: _btn_accept.enabled

    property bool closable: true

    default property alias content: _content.children
    readonly property int defMargin: 10




    parent: Overlay.overlay

    background: Rectangle {
            color: palette.window
//            color: palette.base
        }

    anchors.centerIn:parent
    
    width: 600
    height: 450
    modal: false
    closePolicy: closable? Popup.CloseOnEscape : Popup.NoAutoClose
    dim: true
    visible: false

    signal reject()

    signal accept()

    /*
    MouseArea {
        anchors.fill: parent
        property point lastMousePos: Qt.point(0, 0)
        onPressed: {
            lastMousePos = Qt.point(mouseX, mouseY);
        }
        onMouseXChanged: {
            _base.x += (mouseX - lastMousePos.x)
        }
        onMouseYChanged:{
            _base.y += (mouseY - lastMousePos.y)
        }
    }
    */

    enter: Transition {
        NumberAnimation {
            property: "opacity";
            from: 0.0; to: 1.0
            duration: 500
            easing.type:  Easing.InCubic
        }
    }
    exit: Transition {
        NumberAnimation {
            property: "opacity";
            from: 1.0;
            to: 0.0
            duration: 500
            easing.type:  Easing.OutCubic
        }
    }


    TitleText{
        id: _title
        anchors{
            horizontalCenter: parent.horizontalCenter
            top: parent.top
            topMargin: 20
        }
        text: Qt.application.name
        horizontalAlignment: Text.AlignHCenter
        width: parent.width - 20 * 2
        sub: true
    }

    Base{
        id: _content
        clip: true
        anchors{
            top: _title.bottom
//            left: parent.right
//            right: parent.right
            horizontalCenter: parent.horizontalCenter
            margins: defMargin
            topMargin: defMargin * 2
        }
        width: parent.width - defMargin * 2
        height: _base.height - 170


        //color: palette.button
        //radius: 20
    }

    XemLine{
        id: _bottom_line
        anchors{
            left: parent.left
            right: parent.right
            margins: defMargin
            bottom:  _btn_ok.top
        }
        blue: false


    }


    BigBlueButton{
        id: _btn_ok
        text: qsTr("Ok")
        anchors{
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 10
        }

        onClicked: {
            reject();
            close()
        }
        width: _content.width
        height: 40
    }
    Row{
        id: _approve_btns
        visible: !_btn_ok.visible
        anchors{
            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            bottomMargin: 10
        }
        spacing: 20

        BigBlueButton{
            id: _btn_accept
            text: qsTr("Ok")
            width: _content.width * 0.25
            onClicked: {
                accept()
            }
            focus: true
            Keys.onEnterPressed: {
                accept()
            }
        }
        BigBlueButton{
            id: _btn_reject
            text: qsTr("Cancel")
            width: _content.width * 0.25
            onClicked: {
                reject();
                close()
            }
        }
    }
}

