import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/constants.js" as Const

TabButton {

  id: _btn
  background: Rectangle {
//      implicitWidth: 70
      implicitHeight: Const.xemBtnHeight
      opacity: enabled ? 1 : 0.3
      /*
      gradient: ConicalBg{
      colorOne: _btn.checked ? palette.highlight : palette.button
      colorTwo: _btn.checked ? _btn.hovered ? Qt.darker(palette.highlight) : palette.highlight : _btn.hovered ? palette.highlight : palette.mid
      }
      */
        color: _btn.checked ? palette.highlight : hovered? palette.midlight: palette.base

      radius: Const.xemRectRadius
  }
  contentItem:
      Text {
        text: _btn.text
        color: _btn.checked ? palette.highlightedText : palette.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font{
            underline: hovered
            pixelSize: 14
        }
    }

}
