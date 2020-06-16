import QtQuick 2.12
import QtQuick.Controls 2.12

ComboBox {
    id: _base

    //  property alias notEditable: _input.readOnly
     property bool notEditable: false

    height: 30

    spacing: 5
    leftPadding: 5
    rightPadding: 30


    textRole: "name"
    font: simpleFont

    Component.onCompleted: {
        console.log(_base.model);
    }
    /*
    delegate: ItemDelegate {
              width: _base.width
              height: _base.height
              contentItem: Text {
                  text: modelData
                //   color: highlighted? palette.highlightedText: palette.mid
                  color: palette.mid
                  font: _base.font
                  elide: Text.ElideRight
                  verticalAlignment: Text.AlignVCenter
              }
              background: Rectangle{
                  implicitWidth: _base.width
//                  implicitHeight: 15
                //   color: highlighted? palette.highlight : palette.base
                color: palette.base
              }

              highlighted: _base.highlightedIndex === index

          }
          indicator:  Canvas {
              id: canvas
              contextType: "2d"
              x: _base.width - width - 5 //- _base.rightPadding
              y: _base.topPadding + (_base.availableHeight - height) / 2
              implicitWidth:  20
              implicitHeight: 8


              Connections {
                  target: _base
                  onPressedChanged: canvas.requestPaint()
              }

              onPaint: {
                  context.reset();
                  context.moveTo(0, 0);
                  context.lineTo(width, 0);
                  context.lineTo(width * 0.5 , height);
                  context.closePath();
                  context.fillStyle = _base.subColor
                  context.fill();
              }
          }
          contentItem: TextInput {
              id: _input
              leftPadding: 			10
              rightPadding: 		10//_base.indicator.width + _base.spacing

              text: 				_base.displayText
              font: 				_base.font
              color: 				palette.text
              verticalAlignment: 	Text.AlignVCenter
              horizontalAlignment: 	Text.AlignLeft
              selectByMouse: 		true
              renderType:			Text.NativeRendering
          }

          background: Rectangle {
              implicitWidth: 120
              implicitHeight: _base.height
              //border.color: _base.pressed ? "#17a81a" : "#21be2b"
              //border.width: _base.visualFocus ? 2 : 1
              radius: 1
              color: palette.base

              XemLine{
                  anchors{
                      top: parent.top
                  }
                  width: _base.width
              }
              XemLine{
                  anchors{
                      bottom: parent.bottom
                  }
                  width: _base.width
              }
          }

          popup: Popup {
              y: _base.height - 1
              width: _base.width
              implicitHeight: contentItem.implicitHeight
              padding: 1

              contentItem: ListView {
                  clip: true
                  implicitHeight: contentHeight
                  model: _base.popup.visible ? _base.delegateModel : null
                  currentIndex: _base.highlightedIndex

                  ScrollIndicator.vertical: ScrollIndicator { }

              }

              background: Rectangle {
                  color: palette.text
              }
          }
    */
}
