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

    readonly property var detailsNameMap: {
        "hash"          : qsTr("Hash"),
        "time"          : qsTr("Received Time"),
        "size"          : qsTr("Size"),
        "weight"        : qsTr("Weight"),
        "block_index"   : qsTr("Included in Block"),
        "fee"           : qsTr("Fees")
    }

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
                        BLayout.fillHeight: true
                        BLayout.preferredWidth: parent.width / 2
                        text: model.key
                    }
                    BLabel {
                        BLayout.fillHeight: true
                        BLayout.preferredWidth: parent.width / 2
                        text: model.value
                        elide: Text.ElideRight
                    }
                    BDialogSeparator {
                        BLayout.preferredHeight: 1
                        BLayout.alignment: Qt.AlignBottom
                    }
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
                    BLabel { //TODO Rectangle
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
                        BLabel {
                            text: "(0.0 sat/B - 0.0 sat/WU - 0 bytes)"
                        }
                        BLabel {
                            text: "(0.0 sat/vByte - 0 virtual bytes)"
                        }
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
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("From")
                    }
                    Column {
                        BLayout.preferredWidth: parent.width / 2
                        BLabel {
                            text: model.fromAddress
                        }
                        BLabel {
                            text: model.fromAmount
                        }
                    }
                    BDialogSeparator{}
                    BLabel {
                        BLayout.preferredWidth: parent.width / 2
                        text: qsTr("To")
                    }
                    Column {
                        BLayout.preferredWidth: parent.width / 2
                        BLabel {
                            text: model.toAddress1
                        }
                        BLabel {
                            text: model.toAmount1
                        }
                        BLabel {
                            text: model.toAddress2
                        }
                        BLabel {
                            text: model.toAmount2
                        }
                    }
                    BDialogSeparator{}
                }
            }
        }
    }

    function request(tx) {
        const xhr = new XMLHttpRequest()

        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.HEADERS_RECEIVED) {

            } else if (xhr.readyState === XMLHttpRequest.DONE) {

                if (xhr.status != 200) {
                    // TODO: Error message
                    return;
                }

                _model.clear()
                const response = JSON.parse(xhr.responseText.toString())

                _model.append({
                    title: "Summary",
                    amount: ("%1 BTC").arg((response["inputs"][0]["prev_out"]["value"] - response["fee"]) / _base.precision),
                    fee: ("%1 BTC").arg(response["fee"] / _base.precision),
                    hash: response["hash"],
                    date: new Date(response["time"]).toString(),
                    fromAddress: response["inputs"][0]["prev_out"]["addr"],
                    fromAmount: ("%1 BTC").arg(response["inputs"][0]["prev_out"]["value"] / _base.precision),
                    toAddress1: response["out"][0]["addr"],
                    toAddress2: response["out"][1]["addr"],
                    toAmount1: ("%1 BTC").arg(response["out"][0]["value"] / _base.precision),
                    toAmount2: ("%1 BTC").arg(response["out"][1]["value"] / _base.precision)
                })

                for (var item in response) {
                    if (detailsNameMap.hasOwnProperty(item))
                        _model.append({title: "Details", key: detailsNameMap[item], value: response[item].toString() })

                    if (item === "inputs") {
                        var inputs_list = response[item];

                        for (var i = 0; i < inputs_list.length; ++i) {
                            var obj = inputs_list[i];

                            _model.append({
                                title: "Inputs",
                                indexVal: obj["index"],
                                addressVal: obj["prev_out"]["addr"],
                                vVal: ("%1 BTC").arg(obj["prev_out"]["value"] / _base.precision),
                                scriptVal: obj["prev_out"]["script"],
                                witnessVal: obj["witness"],
                            })
                        }
                    }

                    if (item === "out") {
                        var out_list = response[item];

                        for (var i = 0; i < out_list.length; ++i) {
                            var obj = out_list[i];

                            _model.append({
                                title: "Outputs",
                                indexVal: obj["n"],
                                detailsVal: obj["spent"],
                                addressVal: obj["addr"],
                                vVal: ("%1 BTC").arg(obj["value"] / _base.precision),
                                pkscriptVal: obj["script"],
                            })
                        }
                    }
                }
            }
        }
        xhr.open("GET", _base.url + tx)
        xhr.send()
    }
}
