import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12


CheckBox {
  id: _base
   property string mainColor: palette.text
   property string subColor: palette.base
  property alias wrapMode: _text.wrapMode
  antialiasing: true

  height: 20

  signal goLink(string link)


   font{
       pixelSize: 16
   }

  indicator: CheckBoxIndicator{
      x: _base.leftPadding
      checked: _base.checked
      bgColor: mainColor
      fgColor: subColor
      color: mainColor
  }

  contentItem: Text {
      id: _text
      text: _base.text
      font: _base.font
      opacity: enabled ? 1.0 : 0.3
      color: mainColor
      verticalAlignment: Text.AlignVCenter
      leftPadding: _base.indicator.width + _base.spacing
      wrapMode: Text.Wrap
      onLinkActivated: {
          goLink(link)
      }
      /*
        layer{
            enabled: true
            effect:  DropShadow {
                horizontalOffset: 3
                verticalOffset: 3
                radius: 10.0
                samples: 20
                color: "#80000000"
                source: _text
            }
        }
        */
  }
}
