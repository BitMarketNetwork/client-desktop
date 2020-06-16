import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"


Popup {
    id: _base
    parent: Overlay.overlay

    function wait(ms){
        _base.visible = true;
        if(ms){
            _timer.interval = ms * 1e3;
            _timer.restart();
        }
    }

    function stop(){
        _base.visible = false;
        _timer.running = false;
    }

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
    background:
        Rectangle {
            //radius: 20
            color: palette.base
        }

    anchors.centerIn:parent

    modal: false
    closePolicy: Popup.NoAutoClose
    dim: true
    visible: false

    Spinner{
        anchors{
            centerIn:parent
        }
        width: 200
        height: 200
    }

    Timer{
        id: _timer
        onTriggered: {
            _base.stop()
        }
    }

}
