import QtQuick 2.12

Base {

    property alias name: _title.text
    property alias bold: _title.font.bold

    readonly property int controlWidth: 400

    height: 50
    antialiasing: true

    Text {
        id: _title
        anchors{
            left: parent.left
            leftMargin: 40
            verticalCenter: parent.verticalCenter
        }

        font: simpleFont
        color: palette.mid
    }
}
