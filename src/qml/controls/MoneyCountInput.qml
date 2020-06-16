import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"


Base {
    id: _base

    property alias amount: _amount.text
    property alias unit: _unit.text
    property alias color: _amount.color
    property alias maxLength: _amount.maximumLength
    property int   amoutWidth: _amount.width

    antialiasing: true

    width: 250
    height: 30

    signal wheelUp()
    signal wheelDown()
    signal edit()

        MoneyField{
            id: _amount
            anchors{
                left: parent.left
//                top: parent.top
                verticalCenter: parent.verticalCenter
                right: _unit.left
                rightMargin: 20
            }
            color: _base.color
            height: parent.height
            onChanged: {
                _base.edit()
            }
            onWheelDown: _base.wheelDown()
            onWheelUp: _base.wheelUp()
        }
        /*/
        TextField{
            id: _amount
            anchors{
                left: parent.left
//                top: parent.top
                verticalCenter: parent.verticalCenter
            }
            font{
                pixelSize: _base.fontSize
            }
            selectByMouse: true
            width: 200
            background: Rectangle{
                color: "yellow"
            }
        }
        */

        Label{
            id: _unit
            anchors{
                right: parent.right
                //horizontalCenter: _amount.horizontalCenter
                bottom: parent.bottom
                top: parent.top
            }
            color: _amount.color
            width: 70
            verticalAlignment: Qt.AlignVCenter
        }
}
