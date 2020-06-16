import QtQuick 2.12
import QtGraphicalEffects 1.12



Base {
    id: _base
    property alias icon: _icon.source
    property alias text: _text.text
    // TODO:

    property int icon_size: 45

    property bool selected: false

    signal clicked()

    width: 100
    height: 90


        Image {
            id: _icon
            sourceSize.width: icon_size
            sourceSize.height: icon_size
            height: icon_size
            width: icon_size
            visible: _base.enabled

            anchors{
                top: parent.top
                horizontalCenter: parent.horizontalCenter
            }
        }
        ColorOverlay{
            id: _overlay
            anchors.fill: _icon
            source: _icon
            visible: !_base.enabled
            color: palette.mid
        }
        /*
        DropShadow {
            visible: _overlay.visible
            anchors.fill: _overlay
            horizontalOffset: 5
            verticalOffset: 3
            radius: 8.0
            samples: 20
            color: _base.selected? palette.highlight : palette.base
            source: _overlay
        }
        */

        LabelText {
            id: _text
            enabled: _base.enabled
            anchors{
                top: parent.top
                topMargin: icon_size + 5
                horizontalCenter: parent.horizontalCenter
            }
        }

        MouseArea{
            anchors{
                fill: parent
            }

            onClicked: {
                if(_base.enabled){
                    _base.clicked();
                }
            }
        }
}
