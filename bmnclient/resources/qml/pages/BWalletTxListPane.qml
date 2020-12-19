import "../application"
import "../basiccontrols"
import "../coincontrols"

BPane {
    id: _base
    property string title: qsTr("History")
    property BCoinObject coin: null

    contentItem: BTxListView {
        model: _base.coin.txListModel
        delegate: BTxItem {
            tx: BTxObject {
                coin: _base.coin
                hash: model.name
                height: model.block
                confirmationCount: model.confirmCount
                status: model.status
                timeHuman: model.timeHuman

                amount.valueHuman: BBackend.settingsManager.coinBalance(model.balance)
                amount.unit: BBackend.coinManager.unit
                amount.fiatValueHuman: "0.00" // TODO model.fiatBalance
                amount.fiatUnit: "USD" // TODO BBackend.coinManager.currency

                feeAmount.valueHuman: model.feeHuman
                feeAmount.unit: BBackend.coinManager.unit
                feeAmount.fiatValueHuman: "0.00" // TODO model.fiatBalance
                feeAmount.fiatUnit: "USD" // TODO BBackend.coinManager.currency

                inputAddressListModel: model.inputsModel
                outputAddressListModel: model.outputsModel
            }
            contextMenu: _contextMenu
        }
    }

    BMenu {
        id: _contextMenu
        property BTxObject tx: null

        BMenuItem {
            text: "TODO" // TODO
        }
    }
}
