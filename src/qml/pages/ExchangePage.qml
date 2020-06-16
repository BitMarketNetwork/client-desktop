import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../widgets"
import "../api"

import "../js/functions.js" as Funcs
import "../js/constants.js" as Constants

BasePage {

    readonly property int pageId: Constants.pageId.exchange
    readonly property variant exchange: CoinApi.exchange

    ExchangeAprovePopup{
        id: _approve
        sendAmount: exchange.sourceAmount
        sendUnit: exchange.sourceCoin.unit
        sendIcon: Funcs.loadImage(exchange.sourceCoin.icon)
        receiveAmount: exchange.targetAmount
        receiveUnit: exchange.targetCoin.unit
        receiveIcon: Funcs.loadImage(exchange.targetCoin.icon)
    }

        InfoLabel{
            anchors{
                horizontalCenter: parent.horizontalCenter
                top: parent.top
                topMargin: 20
            }

            id: _title

            text: qsTr("Make an exchange","Exchange page")

            font{
                pixelSize: 24
            }
        }

        Row{
            id: _middle_row
            anchors{
                top: _title.bottom
                topMargin: 50
                left: parent.left
                right: parent.right
            }
            ExchangeSourcePanel{
                id: _source_pane
                coinModel: exchange.sourceModel
                coinIndex: exchange.sourceIndex
                coinUnit: exchange.sourceCoin.unit
                amount: exchange.sourceAmount
                fiatAmount: exchange.sourceFiatAmount
                coinIcon: Funcs.loadImage(exchange.sourceCoin.icon)
                // inputDecimals: exchange.sourceDecimals
                onCoinSelect: {
                    exchange.sourceIndex = index
                }
                onAmountChange: {
                    exchange.sourceAmount = value
                }
                onWheelUp: exchange.increaseSource()
                onWheelDown: exchange.reduceSource()
            }
            ExchangeTargetPanel{
                id: _target_pane
                coinModel: exchange.targetModel
                coinUnit: exchange.targetCoin.unit
                coinIndex: exchange.targetIndex
                amount: exchange.targetAmount
                fiatAmount: exchange.targetFiatAmount
                coinIcon: Funcs.loadImage(exchange.targetCoin.icon)
                // inputDecimals: exchange.targetDecimals
                onCoinSelect: {
                    exchange.targetIndex = index
                    console.log("target index:" + index)
                }
                onAmountChange: {
                    exchange.targetAmount = value
                }
                onWheelUp: {
                    exchange.increaseTarget()
                }
                onWheelDown: exchange.reduceTarget()
            }
        }
        TxBigButton{
            anchors{
                horizontalCenter: parent.horizontalCenter
                bottom: parent.bottom
                bottomMargin: 100
            }
            text: qsTr("Deal")
            onClicked: {
                _approve.open()
            }
        }

    Image {
        id: _change_img
        source: Funcs.loadImage("exchange-icon.png")
        width: 50
        height: 50
        y: _target_pane.y + _target_pane.height * 0.65
        sourceSize{
            width: 60
            height: 60
        }
        anchors{
            horizontalCenter: parent.horizontalCenter
        }
    }
}
