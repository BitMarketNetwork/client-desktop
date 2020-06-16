import QtQuick 2.12
import QtQuick.Controls 2.12



DialogButtonBox{
    standardButtons: DialogButtonBox.Ok | DialogButtonBox.Cancel
    background: WidgetBG{

    }

    spacing: 20
    anchors.bottom: parent.bottom
    anchors.bottomMargin: 25
}
