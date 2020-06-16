import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"


ComboBox{
    id: _base

    currentIndex: 0
    displayText: _unit.currentText
    textRole: "fullName"
    font{
        pixelSize: 16
    }

    /*
    delegate:  ItemDelegate {
            id: _item
            text: modelData.fullName
            width: parent.width
            highlighted:  ListView.isCurrentItem
            onClicked: {
                _base.currentIndex = model.index;
            }
            contentItem:  InfoLabel{
                text: _item.text
                color: fgColor
                leftPadding: 10
            }
            background: Rectangle{
                color: bgColor
            }
    }
    onAccepted: {

    }
    contentItem:  InfoLabel{
        text: _base.displayText
        color: fgColor
        leftPadding: 20
        topPadding: 8
    }
    background: Rectangle{
        radius: 5
        color: bgColor
        height: 120
    }
    */
}
