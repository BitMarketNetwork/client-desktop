import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQml.Models
import Qt.labs.qmlmodels
import "../application"
import "../basiccontrols"

Page {
    id: _base

    property var coin
    readonly property string url: "https://blockchain.info/"

    header: BExplorerHeader {
        coin: _base.coin

        onSearchTx: (tx) => {
            _base.request(tx)
        }
    }

    ListModel {
        id: _model
    }

    BListView {
        id: _listView
        anchors.fill: parent
        model: _model
        delegate: _chooser

        section.property: "title"
        section.criteria: ViewSection.FullString
        section.delegate: BItemDelegate {
            id: _delegate
            required property string section
            contentItem: BRowLayout {
                BLabel  {
                    font.weight: 700
                    text: section
                }
            }
        }
    }

    DelegateChooser {
        id: _chooser
        role: "type"

        DelegateChoice {
            roleValue: "default"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.key
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.val
                        elide: Text.ElideRight
                    }
                }
            }
        }
        DelegateChoice {
            roleValue: "separator"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2
                    BDialogSeparator{}
                }
            }
        }
        DelegateChoice {
            roleValue: "valuesList"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.key
                    }
                    BColumnLayout {
                        BLayout.preferredWidth: parent.width / 2
                        Repeater {
                            model: valList
                            Column {
                                BLabel { text: address }
                                BLabel { text: val }
                            }
                        }
                    }
                }
            }
        }
    }

    function requestError(status) {
        var message = ""
        switch (status) {
            case 404:
                message = qsTr("Not found.")
                break;
            case 429:
                message = qsTr("Error. Too many requests.")
            default:
                break;
        }

        let notificaion = _applicationManager.createObject(
            _applicationWindow,
            "../basiccontrols/BNotification.qml",
            { "text": message })

        notificaion.x = _applicationWindow.width / 2 - notificaion.width / 2

        if (notificaion !== null) {
            notificaion.onClosed.connect(function () {
                Qt.callLater(notificaion.destroy)
            })
            notificaion.open()
        }
    }

    function formatCoinNumber(value) {
        const locale = BBackend.settings.language.currentName
        return ("%1 %2")
            .arg(Number(value / 1e8).toLocaleString(Qt.locale(locale), 'f', 8))
            .arg(_base.coin.name.toUpperCase())
    }

    function dateFromTimeStamp(value) {
        return new Date(Number(value * 1000)).toLocaleString()
    }

    function request(tx) {
        if (tx.length === 64) {
            requestHashInfo(tx)
        } else {
            requestAddressInfo(tx)
        }
    }

    function requestHashInfo(val) {
        const xhr = new XMLHttpRequest()

        function appendSummary(response) {
            var summaryAmount = 0.0;
            for (var i = 0; i < response["inputs"].length; ++i) {
                var obj = response["inputs"][i];
                summaryAmount += obj["prev_out"]["value"]
            }
            var section = "Summary"
            _model.append({title: section, key: qsTr("Amount"), val: formatCoinNumber(summaryAmount - response["fee"]), type: "default"})
            _model.append({title: section, key: qsTr("Fee"), val: formatCoinNumber(response["fee"]), type: "default"}),
            _model.append({title: section, key: qsTr("Hash"), val: response["hash"], type: "default"})
            _model.append({title: section, key: qsTr("Date"), val: dateFromTimeStamp(response["time"]), type: "default"})
        }

        function appendFrom(inputs) {
            for (var i = 0; i < inputs.length; ++i) {
                var input = inputs[i];
                _model.append({title: "From", key: input["prev_out"]["addr"], val: formatCoinNumber(input["prev_out"]["value"]), type: "default"})
            }
        }

        function appendTo(outs) {
            for (var i = 0; i < outs.length; ++i) {
                var out = outs[i]
                _model.append({title: "To", key: out["addr"], val: formatCoinNumber(out["value"]), type: "default"})
            }
        }
        function appendDetails(response) {
            var section = "Details"
            _model.append({title: section, key: qsTr("Hash"), val: response["hash"], type: "default"})
            _model.append({title: section, key: qsTr("Received Time"), val: dateFromTimeStamp(response["time"]), type: "default"})
            _model.append({title: section, key: qsTr("Size"), val: ("%1 bytes").arg(response["size"]), type: "default"})
            _model.append({title: section, key: qsTr("Weight"), val: response["weight"].toString(), type: "default"})
            _model.append({title: section, key: qsTr("Included in Block"), val: response["block_index"].toString(), type: "default"})
            _model.append({title: section, key: qsTr("Fees"), val:formatCoinNumber(response["fee"]), type: "default"})
        }
        function appendInputs(inputs) {
            var section = "Inputs"
            for (var i = 0; i < inputs.length; ++i) {
                var input = inputs[i]
                _model.append({title: section, key: qsTr("Index"), val: input["index"].toString(), type: "default"})
                _model.append({title: section, key: qsTr("Address"), val: input["prev_out"]["addr"], type: "default"})
                _model.append({title: section, key: qsTr("Value"), val: formatCoinNumber(input["prev_out"]["value"]), type: "default"})
                _model.append({title: section, key: qsTr("Pkscript"), val: input["prev_out"]["script"], type: "default"})
                _model.append({title: section, key: qsTr("Witness"), val: input["witness"], type: "default"})

                if (i < inputs.length - 1) {
                    _model.append({title: section, type: "separator"})
                }
            }
        }
        function appendOutputs(outputs) {
            var section = "Outputs"
            for (var i = 0; i < outputs.length; ++i) {
                var output = outputs[i]
                _model.append({title: section, key: qsTr("Index"), val: output["n"].toString(), type: "default"})
                _model.append({title: section, key: qsTr("Details"), val: output["spent"].toString(), type: "default"})
                _model.append({title: section, key: qsTr("Address"), val: output["addr"], type: "default"})
                _model.append({title: section, key: qsTr("Value"), val: formatCoinNumber(output["value"]), type: "default"})
                _model.append({title: section, key: qsTr("Pkscript"), val: output["script"], type: "default"})

                if (i < outputs.length - 1) {
                    _model.append({title: section, type: "separator"})
                }
            }
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    _model.clear()
                    const response = JSON.parse(xhr.responseText.toString())

                    appendSummary(response)
                    appendFrom(response["inputs"])
                    appendTo(response["out"])
                    appendDetails(response)
                    appendInputs(response["inputs"])
                    appendOutputs(response["out"])
                }
                else {
                    requestError(xhr.status)
                }
            }
        }
        xhr.open("GET", _base.url + "rawtx/" + val, true)
        xhr.send()
    }

    function requestAddressInfo(val) {
        const xhr = new XMLHttpRequest()

        function appendAddressInfo(response) {
            var section = "Address"
            _model.append({title: section, key: qsTr("Address"), val: response["address"], type: "default"})
            _model.append({title: section, key: qsTr("Transactions"), val: response["n_tx"].toString(), type: "default"})
            _model.append({title: section, key: qsTr("Total Received"), val: formatCoinNumber(response["total_received"]), type: "default"})
            _model.append({title: section, key: qsTr("Total Sent"), val: formatCoinNumber(response["total_sent"]), type: "default"})
            _model.append({title: section, key: qsTr("Final Balance"), val: formatCoinNumber(response["final_balance"]), type: "default"})
        }
        function appendTx(txs) {
            for (var i = 0; i < txs.length; ++i) {
                var tx = txs[i]
                var section = "Transactions"
                _model.append({title: section, key: qsTr("Amount"), val: formatCoinNumber(tx["result"]), type: "default"})
                _model.append({title: section, key: qsTr("Fee"), val: formatCoinNumber(tx["fee"]), type: "default"})
                _model.append({title: section, key: qsTr("Hash"), val: tx["hash"], type: "default"})
                _model.append({title: section, key: qsTr("Date"), val: dateFromTimeStamp(tx["time"]), type: "default"})

                var inputs = []
                for (var j = 0; j < tx["inputs"].length; ++j) {
                    var input = tx["inputs"][j]
                    inputs.push({ address: input["prev_out"]["addr"], val: formatCoinNumber(input["prev_out"]["value"])})
                }

                var outputs = []
                for (var j = 0; j < tx["out"].length; ++j) {
                    var out = tx["out"][j]
                    outputs.push({ address: out["addr"], val: formatCoinNumber(out["value"])})
                }
                _model.append({title: section, key: qsTr("From"), valList: inputs, type: "valuesList"})
                _model.append({title: section, key: qsTr("To"), valList: outputs, type: "valuesList"})

                if ( i < txs.length - 1) {
                    _model.append({title: section, type: "separator"})
                }
            }
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    _model.clear()
                    const response = JSON.parse(xhr.responseText.toString())

                    appendAddressInfo(response)
                    appendTx(response["txs"])
                }
                else {
                    requestError(xhr.status)
                }
            }
        }
        xhr.open("GET", _base.url + "rawaddr/" + val, true)
        xhr.send()
    }
}
