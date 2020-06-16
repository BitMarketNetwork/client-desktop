import QtQuick 2.12
import QtQuick.Controls 2.12

MenuItem {
    id: _base

    contentItem:
        Text{
      text: _base.text
            font.family: "Arial"
            font.pixelSize: 12
            font.bold: checked
//            font.underline: checked
      opacity: enabled ? 1.0 : 0.3
      color:_base.highlighted ? palette.highlight : palette.text

      horizontalAlignment: Text.AlignLeft
      verticalAlignment: Text.AlignVCenter
      elide: Text.ElideRight
    }

    indicator: Item{}

    background: Rectangle{
       color: "transparent"
//        color: checked? palette.midlight: "transparent"
//        border{
//            width: 2
//            color: checked? palette.dark: "transparent"

//        }

        radius: 5
    }
}
