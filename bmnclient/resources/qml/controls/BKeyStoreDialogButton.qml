import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BButton {
    id: _base
    flat: true
    property alias imagePath: _iconImage.source
    property alias title: _title.text
    property alias details: _details.text

    contentItem: BGridLayout {
        columns: 2
        columnSpacing: 5

        BIconImage {
            id: _iconImage
            BLayout.rowSpan: parent.columns
            sourceSize.width: _applicationStyle.icon.normalWidth
            sourceSize.height: _applicationStyle.icon.normalHeight
            color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        }
        BLabel {
            id: _title
            BLayout.fillWidth: true
            font.bold: true
        }
        BLabel {
            id: _details
            BLayout.fillWidth: true
        }
    }
}