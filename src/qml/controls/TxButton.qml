import QtQuick 2.12
import QtQuick.Controls 2.12
//import QtGraphicalEffects 1.12


Button {
    id: _base
    height: 40

    property alias fontSize: _text.font.pixelSize



    background: Rectangle{
        id: _rect
        color: enabled?hovered?palette.midlight:palette.base: palette.midlight
        radius: 2
        height: _base.height
        width: _base.width
        XemLine{
            anchors.top: parent.bottom
            width: _base.width
        }
    }
    contentItem: Text {
            id: _text
              text: _base.text
              font{
                  underline: hovered
                  pixelSize: 14
              }

              opacity: enabled ? 1.0 : 0.3
              color: palette.text
              horizontalAlignment: Text.AlignHCenter
              verticalAlignment: Text.AlignVCenter
              elide: Text.ElideRight
          }

}
