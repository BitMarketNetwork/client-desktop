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
    readonly property string url: "https://blockchain.info/rawtx/"
    readonly property int precision: 100000000

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
        role: "title"

        DelegateChoice {
            roleValue: "Details"

           BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Hash")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsHash
                        elide: Text.ElideRight
                    }
                    BDialogSeparator {}

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Received Time")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsTime
                        elide: Text.ElideRight
                    }
                    BDialogSeparator {}

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Size")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsSize
                    }
                    BDialogSeparator {}

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Weight")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsWeight
                    }
                    BDialogSeparator {}

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Included in Block")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsBlock
                    }
                    BDialogSeparator {}

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Fees")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsFees
                    }
                    BDialogSeparator {}
                }
            }
        }

        DelegateChoice {
            roleValue: "Inputs"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Index")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.indexVal
                    }
                    BDialogSeparator{}
                    /*BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Details")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsVal
                    }*/
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Address")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.addressVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Value")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.vVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Pkscript")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.scriptVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Witness")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.witnessVal
                        wrapMode: Text.Wrap
                    }
                    BDialogSeparator{}
                }
            }
        }

        DelegateChoice {
            roleValue: "Outputs"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Index")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.indexVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Details")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.detailsVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Address")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.addressVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Value")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.vVal
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Pkscript")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.pkscriptVal
                    }
                    BDialogSeparator{}
                }
            }
        }

        DelegateChoice {
            roleValue: "Summary"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Amount")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.amount
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Fee")
                    }
                    Column {
                        BLayout.preferredWidth: parent.width / 2
                        BLabel {
                            text: model.fee
                        }
                        /*BLabel {
                            text: "(0.0 sat/B - 0.0 sat/WU - 0 bytes)"
                        }
                        BLabel {
                            text: "(0.0 sat/vByte - 0 virtual bytes)"
                        }*/
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Hash")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.hash
                        elide: Text.ElideRight
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("Date")
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.date
                    }
                    BDialogSeparator{}
                }
            }
        }

        DelegateChoice {
            roleValue: "From"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.fromAddress
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.fromAmount
                    }
                    BDialogSeparator{}
                }
            }
        }

        DelegateChoice {
            roleValue: "To"

            BItemDelegate {
                contentItem: BGridLayout {
                    columns: 2

                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.toAddress
                    }
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: model.toAmount
                    }
                    BDialogSeparator{}
                }
            }
        }
    }

    function request(tx) {
        const xhr = new XMLHttpRequest()

        function requestError() {
            let notificaion = _applicationManager.createObject(
                _applicationWindow,
                "../basiccontrols/BNotification.qml",
                { "text": qsTr("Transaction not found.") })

            notificaion.x = _applicationWindow.width / 2 - notificaion.width / 2

            if (notificaion !== null) {
                notificaion.onClosed.connect(function () {
                    Qt.callLater(notificaion.destroy)
                })
                notificaion.open()
            }
        }

        function parseSummary(response) {
            var summaryAmount = 0.0;
            for (var i = 0; i < response["inputs"].length; ++i) {
                var obj = response["inputs"][i];
                summaryAmount += obj["prev_out"]["value"]
            }

            return {
                title: "Summary",
                amount: ("%1 BTC").arg((summaryAmount - response["fee"]) / _base.precision),
                fee: ("%1 BTC").arg(response["fee"] / _base.precision),
                hash: response["hash"],
                date: new Date(response["time"] * 1000).toLocaleString()
            }
        }
        function parseFrom(input) {
            return {
                title: "From",
                fromAddress: input["prev_out"]["addr"],
                fromAmount: ("%1 BTC").arg(input["prev_out"]["value"] / _base.precision)
            }
        }
        function parseTo(out) {
            return {
                title: "To",
                toAddress: out["addr"],
                toAmount: ("%1 BTC").arg(out["value"] / _base.precision)
            }
        }
        function parseDetails(response) {
            return {
                title: "Details",
                detailsHash: response["hash"],
                detailsTime: new Date(Number(response["time"] * 1000)).toLocaleString(),
                detailsSize: ("%1 bytes").arg(response["size"]),
                detailsWeight: response["weight"],
                detailsBlock: response["block_index"],
                detailsFees: ("%1 BTC").arg(response["fee"] / _base.precision)
            }
        }
        function parseInputs(input) {
            return {
                title: "Inputs",
                indexVal: input["index"],
                addressVal: input["prev_out"]["addr"],
                vVal: ("%1 BTC").arg(input["prev_out"]["value"] / _base.precision),
                scriptVal: input["prev_out"]["script"],
                witnessVal: input["witness"],
            }
        }
        function parseOutputs(output) {
            return {
                title: "Outputs",
                indexVal: output["n"],
                detailsVal: output["spent"],
                addressVal: output["addr"],
                vVal: ("%1 BTC").arg(output["value"] / _base.precision),
                pkscriptVal: output["script"],
            }
        }

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status !== 200) {
                    requestError()
                    return;
                }
                _model.clear()
                const response = JSON.parse(xhr.responseText.toString())

                _model.append(parseSummary(response))

                for (var i = 0; i < response["inputs"].length; ++i) {
                    _model.append(parseFrom(response["inputs"][i]))
                }

                for (var i = 0; i < response["out"].length; ++i) {
                    _model.append(parseTo(response["out"][i]))
                }

                _model.append(parseDetails(response))

                for (var i = 0; i < response["inputs"].length; ++i) {
                    _model.append(parseInputs(response["inputs"][i]))
                }

                for (var i = 0; i < response["out"].length; ++i) {
                    _model.append(parseOutputs(response["out"][i]))
                }
            }
        }
        xhr.open("GET", _base.url + tx)
        xhr.send()
    }
}
