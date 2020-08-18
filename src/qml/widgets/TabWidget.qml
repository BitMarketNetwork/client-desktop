import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/functions.js" as Funcs
import "../controls"
import "../api"

Base {
      id: _base
      default property alias content: _stack.children

      property int current: 0

      onCurrentChanged: setOpacities()
      Component.onCompleted: setOpacities()

      function setOpacities() {
        //   console.log(`new tab ${current} for ${_stack.children.length}`)
          for (var i = 0; i < _stack.children.length; ++i) {
              _stack.children[i].opacity = (i === current ? 1 : 0);
              _stack.children[i].enabled = i === current;
          }
      }

      TitleText{
          id: _title
          anchors{
            top: parent.top
            topMargin: 10
            left: parent.left
          }
          text: qsTr("Application settings","Menu item")
      }

      XemLine{
          anchors.top: _header.bottom
      }

      Row {
          id: _header

          width: parent.width
          anchors{
            top: _title.bottom
            topMargin: 10
            left: parent.left
          }

          Repeater {
              id: _view
              model: _stack.children.length
//              spacing: 10
              delegate:

                      TabHandler{
                          id: _btn

                            text: 	_stack.children[index].title
                            width: Math.min(180, parent.width / _stack.children.length)
                            height: 40
                            checked: current === index
                            MouseArea {
                                anchors.fill: parent
                                onClicked: _base.current = index
                              }
//                    }
              }

          }
      }

      Base {
          id: _stack
          width: _base.width
          anchors{
              top: _header.bottom
              bottom: _base.bottom
              left: parent.left
          }
      }
  }
