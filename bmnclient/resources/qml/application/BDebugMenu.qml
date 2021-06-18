import "../application"
import "../basiccontrols"

BMenu {
    title: "Debug"

    BMenu {
        title: "Coins"
        BMenuItem {
            text: "Increase height"
            onTriggered: {
                BBackend.debugManager.increaseHeight(1)
            }
        }
        BMenuItem {
            text: "Decrease height"
            onTriggered: {
                BBackend.debugManager.increaseHeight(-1)
            }
        }
    }


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
            text: "Increment coin block height"
            onTriggered: {
                // TODO dont work, no visual changes
                //BBackend.coinManager.coin.height += 1
            }
        }
        BMenuItem {
            text: "Clear all wallets"
            onTriggered: {
                // TODO bad name
                //BBackend.coinManager.clear()
            }
        }
    }
    BMenu {
        title: "Network"
        BMenu {
            title: "Undo transactions"
            BMenuItem {
                text: "1"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    //BBackend.debugManager.undoTransaction(1)
                }
            }
            BMenuItem {
                text: "2"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    //BBackend.debugManager.undoTransaction(2)
                }
            }
        }
    }
}
