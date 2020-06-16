import QtQuick 2.12

Rectangle {
    id: _base

    property string bgColor: _border.color
    property alias fgColor: _rect.color
    property alias checked: _rect.visible

      implicitWidth: 26
      implicitHeight: 26
      y: parent.height / 2 - height / 2
      radius: 3
      border{
          id:_border
      }

      Rectangle {
          id: _rect
          width: 14
          height: 14
          x: 6
          y: 6
          radius: 2
      }
  }
