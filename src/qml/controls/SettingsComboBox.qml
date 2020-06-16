import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"
import "../js/functions.js" as Funcs
import "../js/constants.js" as Const

SettingsControl {
    id: _base
    property alias model: _combo.model
    property alias role: _combo.textRole
    property alias index: _combo.currentIndex

    signal select(int index)



        ComboBox{
            id: _combo
            anchors{
                right: parent.right
                rightMargin: 20
                left: parent.left
                leftMargin: 200
                verticalCenter: parent.verticalCenter
            }
            font: simpleFont
            textRole: "objectName"

            width: controlWidth
            onActivated: select(currentIndex)

            background: Rectangle{
                         XemLine{
                             width: parent.width
                             anchors.top: parent.top
                         }
                         XemLine{
                             width: parent.width
                             anchors.bottom: parent.bottom
                         }
                    radius: Const.xemRectRadius
                    color: palette.base
            }

            popup: Popup {
                     y: _combo.height - 1
                     width: _combo.width
                     implicitHeight: contentItem.implicitHeight
                     padding: 1

                     contentItem: ListView {
                         clip: true
                         implicitHeight: contentHeight
                         model: _combo.popup.visible ? _combo.delegateModel : null
                         currentIndex: _combo.highlightedIndex

                         ScrollIndicator.vertical: ScrollIndicator { }

                     }

                     background: Rectangle {
                         border.color: palette.toolTipText
                         radius: 2
                         color: palette.button
                     }
                 }
            /*
            onHighlighted: {
                console.log(`CB item pick up ${index} ${_name.text}`)
            }
            */
      }

        /*

        Component.onCompleted: {
            console.trace();
            Funcs.explore(_combo.model)
        }

        */
}
