import "../application"
import "../basiccontrols"

BMenu {
    title: "Debug"

    BMenu {
        title: "UI tests"
        BMenuItem {
            text: "OS notification test"
            onTriggered: {
                BBackend.uiManager.notify(
                            "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore...",
                            3)
            }
        }
    }
    BMenu {
        title: "Wallet management"
        BMenuItem {
            text: "UTXO list"
            onTriggered: {
                BBackend.coinManager.getAddressUnspentList()
            }
        }
        BMenuItem {
            text: "Increment coin block height"
            enabled: BBackend.coinManager.coinIndex >= 0
            onTriggered: {
                // TODO dont work, no visual changes
                BBackend.coinManager.coin.height += 1
            }
        }
        BMenuItem {
            text: "Clear all wallets"
            onTriggered: {
                // TODO bad name
                BBackend.coinManager.clear()
            }
        }
    }
    BMenu {
        title: "Network"
        BMenuItem {
            text: "Poll"
            onTriggered: {
                // TODO cannot test, not found ui visual updates
                debugManager.poll()
            }
        }
        BMenuItem {
            text: "Stop polling"
            onTriggered: {
                // TODO cannot test, not found ui visual updates
                debugManager.stopPolling()
            }
        }
        BMenuItem {
            text: "Update fees"
            onTriggered: {
                // TODO cannot test, not found ui visual updates
                debugManager.retrieveFee()
            }
        }
        BMenu {
            title: "Undo transactions"
            enabled: BBackend.coinManager.coinIndex >= 0
            BMenuItem {
                text: "1"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    BBackend.debugManager.undoTransaction(BBackend.coinManager.coinIndex, 1)
                }
            }
            BMenuItem {
                text: "2"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    BBackend.debugManager.undoTransaction(BBackend.coinManager.coinIndex, 2)
                }
            }
        }
    }
    BMenu {
        title: "Debug scenarios"
        BMenuItem {
            text: "Online mode"
            onTriggered: {
                BBackend.uiManager.online = !BBackend.uiManager.online
            }
        }
    }
}
