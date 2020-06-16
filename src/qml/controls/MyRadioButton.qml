import QtQuick 2.0
import QtQuick.Controls 2.12
import "../controls"


RadioButton {
    id: _base
    spacing: 100


    indicator: Rectangle {
                id: _indicator
              implicitWidth: 26
              implicitHeight: 26
              x: _base.leftPadding
              y: parent.height / 2 - height / 2
              radius: 13
              border.color: palette.highlight

              Rectangle {
                  width: 14
                  height: 14
                  x: 6
                  y: 6
                  radius: 7
                  color: checked? palette.mid:palette.highlightedText
                  visible: _base.checked
              }
          }

    /*TODO: WTF? why this asshole doen't work*/
    /*
    contentItem: Text {
              text: _base.text
              font: _base.font
              opacity: enabled ? 1.0 : 0.3
//              color: palette.mid
              color: "blue"
              verticalAlignment: Text.AlignVCenter
          }
          */


    XemLine{
        anchors{
            bottom: parent.bottom
            left: _indicator.right
            right: parent.right
            leftMargin: 20
            rightMargin: -20
        }
    }

    Component.onCompleted: {
        /*WA*/
        contentItem.color = palette.mid;
        contentItem.font = simpleFont
    }

}
