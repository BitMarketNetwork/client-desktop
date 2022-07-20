import QtQml
import "../application"
import "../basiccontrols"

BColumnLayout {
    id: _base

    property var coin
    readonly property string url: "https://api.blockchain.info/"
    readonly property string name: _base.coin.name.toUpperCase()
    signal searchTx(string tx)

    property string priceValue
    property string hashRateValue
    property string txValue
    property string txVolumeValue
    property string txVolumeEstValue

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
    BControl {
        BLayout.alignment: Qt.AlignHCenter
        BLayout.fillWidth: true

        contentItem: BGridLayout {
            id: _headerGrid
            columns: 5

            BLabel {
                id: price
                BLayout.alignment: Qt.AlignHCenter
                text: _base.priceValue
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: hashRate
                BLayout.alignment: Qt.AlignHCenter
                text: _base.hashRateValue
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: tx
                BLayout.alignment: Qt.AlignHCenter
                text: _base.txValue
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: txVolume
                BLayout.alignment: Qt.AlignHCenter
                text: _base.txVolumeValue
                font.pixelSize: 16
                font.weight: 600
            }
            BLabel {
                id: txVolumeEst
                BLayout.alignment: Qt.AlignHCenter
                text: _base.txVolumeEstValue
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
        }
    }
    BSeparator {
        BLayout.fillWidth: true
    }

    function requestStats() {
        const xhr = new XMLHttpRequest()

        function formatNumber(value, divider, unit, formate, precision) {
            const locale = BBackend.settings.language.currentName
            return ("%1 %2")
                .arg(Number(value / divider).toLocaleString(Qt.locale(locale), formate, precision))
                .arg(unit)
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status != 200) {
                    // TODO: Error message
                    return;
                }
                const response = JSON.parse(xhr.responseText.toString())

                _base.hashRateValue = formatNumber(response["hash_rate"], 1e9, "EH/s", 'f', 3)
                _base.txValue = formatNumber(response["n_tx"], 1, '', '', 0)
                _base.txVolumeValue = formatNumber(response["total_btc_sent"], 1e14, ("m %1").arg(_base.name), 'f', 3)
                _base.txVolumeEstValue = formatNumber(response["estimated_btc_sent"], 1e8, _base.name, '', 0)
            }
        }
        xhr.open("GET", _base.url + "stats")
        xhr.send()
    }

    function requestTicker() {
        const xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status != 200) {
                    // TODO: Error message
                    return;
                }
                const response = JSON.parse(xhr.responseText.toString())
                let currency = BBackend.settings.fiatCurrency.currentName
                _base.priceValue = ("%1 %2")
                    .arg(response[currency]["last"])
                    .arg(currency)
            }
        }
        xhr.open("GET", _base.url + "ticker")
        xhr.send()
    }

    Timer {
        id: _timer
        interval: 5000
        repeat: true
        running: true
        triggeredOnStart: true

        onTriggered: {
            _base.requestTicker()
            _base.requestStats()
        }
    }
}
