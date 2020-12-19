import QtQml 2.15
import "../basiccontrols"

BComboBox {
    id: _base

    signal changed

    displayText: qsTr("Select source addresses")
    popup: BPopup {
        width: Math.max(implicitWidth, _base.width)
        height: implicitHeight
        x: 0
        y: _applicationManager.calcPopupPosition(_base, width, height).y

        contentItem: BColumnLayout {
            BSwitch {
                id: _selectAll
                text: qsTr("Auto selection")
                checked: true
                onCheckedChanged: {
                    let v = checked
                    for (let i in _base.delegateModel.model) {
                        _base.delegateModel.model[i].useAsSource = v
                    }
                    _base.changed()
                }
            }
            BSeparator {
                BLayout.fillWidth: true
            }
            BAddressListView {
                BLayout.fillWidth: true
                visibleItemCount: model && model.length > 0 ? Math.min(6, model.length) : 1
                model: _base.popup.visible ? _base.delegateModel.model : null
                delegate: BAddressItem {
                    id: _item
                    address: BAddressObject {
                        coin: _base.coin
                        name: modelData.name
                        label: modelData.label
                        watchOnly: false
                        updating: false
                        amount.valueHuman: BBackend.settingsManager.coinBalance(modelData.balance)
                        amount.unit: BBackend.coinManager.unit // TODO
                        //amount.fiatValueHuman: modelData.fiatBalance // TODO
                        //amount.fiatUnit: _base.coin.fiatAmountUnit // TODO
                    }
                    // TODO contextMenu: _contextMenu
                    checkable: true
                    onCheckedChanged: {
                        if (checked) {
                            modelData.useAsSource = true
                        } else {
                            modelData.useAsSource = false
                            //_selectAll.checked = false
                        }
                        _base.changed()
                    }

                    Binding {
                        target: _item
                        property: "checked"
                        value: _selectAll.checked || modelData.useAsSource
                    }
                }
                templateDelegate: BAddressItem {
                    address: BAddressObject {
                        coin: _base.tx.coin
                    }
                    // TODO contextMenu: _contextMenu
                    checkable: true
                }
            }
        }
    }
}
