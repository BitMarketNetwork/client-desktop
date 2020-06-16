import QtQuick 2.0
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12

Button {
    id: _base

    property bool pale: false

    height: 40
    Layout.preferredHeight: 40
    Layout.fillWidth: true

    readonly property int iconSize: 24

    background: Rectangle{
        color: {
            if(pale){
                if(hovered){
                    return palette.alternateBase
                }
                return palette.button
            }else{
                if(hovered){
                    return palette.button
                }
                return palette.highlight
            }
        }
    }
    contentItem:
        Base{
            anchors{
//                fill: parent
                horizontalCenter: parent.horizontalCenter
            }

            Image {
                anchors{
                    right: _text.left
                    rightMargin: 5
                    verticalCenter: parent.verticalCenter
                }
                width: iconSize
                height: iconSize
                source: _base.icon.source
                sourceSize.width: iconSize
                sourceSize.height: iconSize
                smooth: true

            }

            Text {
                id: _text
                  text: _base.text
                anchors{
                    verticalCenter: parent.verticalCenter

//                    left: parent.horizontalCenter
//                    leftMargin: 5
                    horizontalCenter: parent.horizontalCenter
                }
                  font{
//                      underline: hovered
                      pixelSize: 14
                  }


                  opacity: enabled ? 1.0 : 0.3
                  color: {

                      if(pale){
                          return palette.base
                      }
                      return palette.highlightedText
                  }
                  horizontalAlignment: Text.AlignHCenter
                  verticalAlignment: Text.AlignVCenter
                  elide: Text.ElideRight
              }
        }
}
