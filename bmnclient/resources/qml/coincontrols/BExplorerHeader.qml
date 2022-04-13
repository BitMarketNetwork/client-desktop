import QtQml
import "../application"
import "../basiccontrols"

BColumnLayout {
    id: _base

    property var coin
    readonly property string url: "https://api.blockchain.info/stats"

    signal searchTx(string tx)

    BControl {
        BLayout.fillWidth: true
        padding: _applicationStyle.padding
        contentItem: BRowLayout {

            BIconLabel {
                BLayout.fillWidth: true
                icon.width: _applicationStyle.icon.largeWidth
                icon.height: _applicationStyle.icon.largeHeight
                icon.source: _applicationManager.imagePath(_base.coin.iconPath)
                font.bold: true
                text: _base.coin.fullName
            }
            BTextField {
                id: transactionInput
                placeholderText: qsTr("Search your transaction")
                text: "ed0bc0ea57620fdfd285935f3338ea0c601d9acb66f0f314f601de5db50c4726"
            }
            BButton { // TODO: icon
                BLayout.leftMargin: 10
                text: "SEARCH"
                enabled: transactionInput.text.length > 0
                onClicked: {
                    _base.searchTx(transactionInput.text)
                }
            }
        }
    }
    BSeparator {
        BLayout.fillWidth: true
    }
    BControl { // TODO: text style\format
        BLayout.alignment: Qt.AlignHCenter
        BLayout.fillWidth: true

        contentItem: BGridLayout {
            id: _headerGrid
            columns: 5

            BLabel {
                id: price
                BLayout.alignment: Qt.AlignHCenter
                //text: "$50,000.00"
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: hashRate
                BLayout.alignment: Qt.AlignHCenter
                //text: "200,000.00 EH/s"
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: tx
                BLayout.alignment: Qt.AlignHCenter
                //text: "200,000"
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: txVolume
                BLayout.alignment: Qt.AlignHCenter
                //text: "3.400m BTC"
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: txVolumeEst
                BLayout.alignment: Qt.AlignHCenter
                //text: "30,000 BTC"
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                BLayout.alignment: Qt.AlignHCenter
                text: qsTr("Price")
                font.pixelSize: 12
            }
            BLabel {
                BLayout.alignment: Qt.AlignHCenter
                text: qsTr("Estimated Hash Rate")
                font.pixelSize: 12
            }
            BLabel {
                BLayout.alignment: Qt.AlignHCenter
                text: qsTr("Transactions (24hrs)")
                font.pixelSize: 12
            }
            BLabel {
                BLayout.alignment: Qt.AlignHCenter
                text: qsTr("Transactions volume")
                font.pixelSize: 12
            }
            BLabel {
                BLayout.alignment: Qt.AlignHCenter
                text: qsTr("Transactions volume (Est)")
                font.pixelSize: 12
            }

            function request() {
                const xhr = new XMLHttpRequest()

                xhr.onreadystatechange = function() {
                    if (xhr.readyState === XMLHttpRequest.HEADERS_RECEIVED) {
                        //print('HEADERS_RECEIVED')
                    } else if(xhr.readyState === XMLHttpRequest.DONE) {
                        //print('DONE')
                        const response = JSON.parse(xhr.responseText.toString())

                        price.text = ("$%1").arg(response["market_price_usd"])
                        hashRate.text = response["hash_rate"]
                        tx.text = response["n_tx"]
                        txVolume.text = response["total_btc_sent"]
                        txVolumeEst.text = response["estimated_btc_sent"]
                    }
                }
                xhr.open("GET", _base.url)
                xhr.send()
            }

            Timer {
                id: _timer
                interval: 5000
                repeat: true
                running: true
                triggeredOnStart: true

                onTriggered: {
                    _headerGrid.request()
                }
            }
        }
    }
    BSeparator {
        BLayout.fillWidth: true
    }
}
