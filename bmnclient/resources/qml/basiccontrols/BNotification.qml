import QtQml
import QtQuick

BPopup {
    id: _base
    focus: false
    closePolicy: BPopup.NoAutoClose
    
    property alias text: _contentLabel.text
    
    Timer {
        id: timer
        interval: 3000
        running: true
        repeat: false
        onTriggered: {
            _base.close()
        }
    }
    contentItem: Item {
        implicitWidth: _contentLabel.implicitWidth
        implicitHeight: _contentLabel.implicitHeight

        MouseArea {
            anchors.fill: parent
            onClicked: {
                _base.close()
            }
        }
        BLabel {
            id: _contentLabel
            anchors.centerIn: parent
        }
    }

    onOpened: {
        timer.start()
    }
}