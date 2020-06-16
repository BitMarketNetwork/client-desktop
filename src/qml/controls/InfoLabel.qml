import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12


Label {
    id: _base
    property bool effect: false
    property bool dark: false

    font{
        pixelSize: 16
      //  family: "Lucida Sans"
    }
    color: palette.text
    anchors.centerIn: parent.center
    antialiasing: true
   // bottomInset: 10
    //bottomPadding: 10
    //topInset: 10
    styleColor: Qt.tint( color , palette.base )
    //style: Text.Sunken
    rightInset: 10
    leftInset: 5
    horizontalAlignment: Text.AlignLeft
    verticalAlignment: Text.AlignVCenter
    wrapMode: Text.WordWrap
    elide: effect? Text.ElideMiddle: Text.ElideNone
    /*
    layer{
        id: _layer
        enabled: _base.enabled && _base.font.pixelSize > 16
        effect:  DropShadow {
            horizontalOffset: 2
            verticalOffset: 2
            radius: 10.0
            samples: 20
            color: dark? palette.dark: palette.midlight
            source: _base
        }
    }
    */
}
