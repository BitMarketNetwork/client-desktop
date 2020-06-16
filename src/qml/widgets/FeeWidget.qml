import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/constants.js" as Constants
import "../controls"
import "../api"
import "../widgets"
import "../pages"


SendWidget {
    id: _base
    title: qsTr("Fee:")
    height: 120


    property alias amount: _amount.amount
    property alias blocksCount: _target.text
    property int confirmTime: -1
    property alias sliderValue: _slider.value
    property alias substractFee: _substract.checked

    signal slider(real value)
    signal input(int value)

    function esteem(){
                var result = null
                const LIMIT = 5;
                console.log(`minutes: ${confirmTime}`)
                if (confirmTime < 0){
                    return qsTr("Transaction will be never confirmed")
                }
                if (confirmTime < LIMIT){
                    result = qsTr("immediately")
                }
                else if(confirmTime < 120){
                    result = qsTr("in %1 minutes").arg(LIMIT * (confirmTime/LIMIT).toFixed())
                }
                else{
                    result = qsTr("in %1 hours").arg((confirmTime/60).toFixed())
                }
                return qsTr("Transaction will be confirmed %1").arg(result)
    }

        Slider{
            id: _slider
            anchors{
//                bottom: _target.top

                left: _amount.left
//                right: _substract.left
//                rightMargin: defMargin
                top: _amount.bottom
                topMargin: 10
            }

            height: 20
            width: 350

            handle: Rectangle{
              width: 6
              height: 15
              x: _slider.leftPadding + _slider.visualPosition * (_slider.availableWidth - width)
              y: _slider.topPadding + _slider.availableHeight / 2 - height / 2
              color: palette.dark
            }

            onValueChanged: {
                slider(value)
            }

            background: Rectangle{
                color: palette.midlight
                width: _slider.width
            }
        }

        Text{
            id: _target
            anchors{
//                bottom: parent.bottom
                top: _slider.bottom
                topMargin: 10
//                bottomMargin: 20
               // horizontalCenter: _slider.horizontalCenter
                left: _slider.left
                leftMargin: 0
            }
            text: esteem()
            font: simpleFont
            color: palette.mid
        }
        SwitchBox{
            id: _substract
            anchors{
                left: _slider.right
                leftMargin: 20

                // both variants are good
//                verticalCenter: _slider.bottom
                verticalCenter: _slider.verticalCenter
            }

            text: qsTr("Substract fee:")
        }

        MoneyCountInput{
            id: _amount
            anchors{
                margins: defMargin
                top: parent.top
                topMargin: 20
                right: parent.right
                left: parent.left
                leftMargin: defLeftMargin
            }
            unit: qsTr("satoshi/byte")
            color: palette.mid
            onEdit: {
                input(amount)
            }
        }
}
