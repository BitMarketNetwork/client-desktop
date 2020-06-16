import QtQuick 2.12
import QtQuick.Controls 2.12


MenuBar {
    background: Rectangle{
        color: palette.button
        radius: 1
    }
    delegate: MenuBarItem {
        id: _menubar_item

        contentItem:
                Text {
            text: _menubar_item.text
            font.family: "Arial"
            font.pixelSize: 12
            font.bold: false

            opacity: enabled ? 1.0 : 0.3
            color: _menubar_item.highlighted ? palette.highlightedText : palette.buttonText
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            leftPadding: 10
        }

        background: Rectangle {
            implicitWidth: 40
            implicitHeight: 40
            opacity: enabled ? 1 : 0.3
            color: _menubar_item.highlighted ? palette.highlight : palette.button
        }
    }
}
