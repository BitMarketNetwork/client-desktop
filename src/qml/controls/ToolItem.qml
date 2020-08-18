import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12


ToolButton{
    id: _base

    antialiasing: true

    property alias pix: _base.icon.source
    readonly property int icon_size: 16

               topPadding: 10
//    spacing: 3
//    width: 80




    contentItem:
        Row{
            spacing: _base.spacing

            Image {
                id: _icon
                source: _base.icon.source
                width: icon_size
                height: icon_size
                smooth: true
                cache: true
                sourceSize{
                    width: icon_size
                    height: icon_size
                }
                anchors{
                    bottom: parent.bottom
                }
            }
        ColorOverlay  {
            anchors.fill: _icon
            source: _icon
            color: palette.midlight
                    visible: !enabled
        }

            Text {
                anchors{
                    bottom: parent.bottom
                }
               text: _base.text
               font{
                   pixelSize: 12
                   bold: _base.checked
               }
//               rightPadding: 10
               opacity: enabled ? 1.0 : 0.3
               color:  enabled? palette.text: palette.midlight
               horizontalAlignment: Text.AlignHCenter
               verticalAlignment: Text.AlignVCenter
               elide: Text.ElideMiddle
             }
        }

    background: Rectangle {
        implicitHeight: 40
        implicitWidth: 60
        opacity: _base.enabled ? 1 : 0.3
//        color: hovered? palette.midlight: "transparent"
//        color: checked? palette.midlight: "transparent"
        radius: 1
    }
}
