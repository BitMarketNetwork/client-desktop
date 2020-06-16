import QtQuick 2.12
import QtQuick.Controls 2.12


Base{
        id: _base
        property alias inputDecimals: _input_validator.decimals
        property alias inputLocale: _input_validator.locale
        property alias fontSize: _input.font.pixelSize
        property alias maximumLength: _input.maximumLength
        property alias text: _input.text
        signal amountChange(string value)
        signal wheelUp()
        signal wheelDown()

//        color: "blue"


    TextInput{
        id: _input

        anchors{
            fill: parent
        }

        selectByMouse: true
        rightPadding: 5
        leftPadding: 5

        focus: true
        maximumLength: 12
        horizontalAlignment: TextInput.AlignHCenter
        verticalAlignment: TextInput.AlignBottom
        validator: DoubleValidator{
            id: _input_validator
            bottom: 0
        }

        onTextEdited: {
        //amountChange(_amount.text)
        }
        onEditingFinished: {
            amountChange(_amount.text)
            focus = false
        }
    }

    MouseArea{
        anchors.fill: parent
        propagateComposedEvents: true
        onClicked: {
            parent.forceActiveFocus();
        }
        onWheel: {
            if(wheel.angleDelta.y > 0){
            wheelUp()
            }else{
            wheelDown()
            }
        }
    }
}
