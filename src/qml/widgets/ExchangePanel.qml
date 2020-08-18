import QtQuick 2.12
import QtQuick.Controls 2.12
import QtGraphicalEffects 1.12
import "../controls"
import "../api"


SendWidget {
    id: _base
    height: 320
    state: onTheLeft?"left":"right"

    property  bool  onTheLeft: false

    property alias coinIcon: _coin_icon.source
    property alias coinModel: _coin.model
    property alias coinUnit: _unit.text
    property alias coinIndex: _coin.currentIndex
    property alias amount: _input.text
    property alias fiatAmount: _currency.amount
    property alias image: _bg_image.source
    // property alias inputDecimals: _input.inputDecimals
    // property alias inputLocale: _input.inputLocale

    readonly property int icon_size: 45

    signal coinSelect(int index)
    signal amountChange(string value)
    signal wheelUp()
    signal wheelDown()

    anchors{
        margins: 30
    }

            Image {
                id: _bg_image
                z: -1
                anchors{
                    /*
                    right: _amount_title.left
                    leftMargin: 30
                    top: _amount_title.top
                    */
                    fill: parent
                }
                opacity: 0.1
                smooth: true
                width: 150
                height: 70
                sourceSize{
                width: 150
                height: 70
                }
                /*
                GaussianBlur {
                anchors.fill: _bg_image
                source: _bg_image
                radius: 8
                samples: 16
                deviation: 0.1
                }
                */
            }

            ExchangeCombo{
                id: _coin

                anchors{
                    //horizontalCenter: parent.horizontalCenter
                    //horizontalCenterOffset: -40
                    top: parent.top
                    topMargin: 80
                    left:  _row.left
                    right: _row.right
                }
                onActivated: {
                    coinSelect(_coin.currentIndex)
                }
            }

        Row{
            id: _row
            anchors{
                verticalCenter: parent.verticalCenter
                horizontalCenter: parent.horizontalCenter
                //horizontalCenterOffset: -40
            }
            x: 200
            spacing: 10
            Image {
                id: _coin_icon
                sourceSize.height: icon_size
                sourceSize.width: icon_size
                height: icon_size
                width: icon_size
                fillMode: Image.PreserveAspectFit
                smooth: true
            }
            MoneyField{
                id: _input
                onWheelDown: _base.wheelDown()
                onWheelUp: _base.wheelUp()
                // onAmountChange: amountChange(value)
                width: 100
            }

            InfoLabel{
                anchors{
                }
                id: _unit
                width: 100
                height: 50

                font{
                    pixelSize: 24
                }
            }
        }

        MoneyCount{
            id: _currency
            anchors{
                horizontalCenter: parent.horizontalCenter
                horizontalCenterOffset: -20
                top: _row.bottom
                topMargin: 30
            }
            unit: CoinApi.coins.currency
            fontSize: 24
        }
        /*
        ColorOverlay{
            id: _overlay
            anchors.fill: _bg_image
            source: _bg_image
            visible: true
            color: "#11111111"
            opacity: 0.1
        }

        GaussianBlur {
            anchors.fill: _bg_image
            source: _overlay
            radius: 8
            samples: 16
            opacity: 0.1
            deviation: 4
        }
        LevelAdjust {
            anchors.fill: _bg_image
            source: _bg_image
            minimumOutput: "#00ffffff"
            maximumOutput: "#ff000000"
        }
        */

        /*
        states: [
            State {
                name: "left"
               when: onTheLeft
                AnchorChanges{
                    target: _bg_image
                    anchors.right: parent.right
                }
                PropertyChanges {
                    target: _bg_image
                    anchors.rightMargin: 50
                }
            },
            State {
                name: "right"
                when: !onTheLeft
                AnchorChanges{
                    target: _bg_image
                    anchors.left: parent.left
                }
                PropertyChanges {
                    target: _bg_image
                    anchors.leftMargin: 50
                }
            }
        ]
        */

}
