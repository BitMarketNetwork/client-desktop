import "../application"
import "../basiccontrols"

BMenu {
    title: "Debug"

    BMenu {
        title: "UI tests"
        BMenuItem {
            text: "Insert TX"
            enabled: BBackend.coinManager.addressIndex >= 0
            onTriggered: {
                BBackend.coinManager.addTxRow()
            }
        }
        BMenuItem {
            text: "OS notification test"
            onTriggered: {
                BBackend.uiManager.notify(
                            "Notification test",
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
            text: "Toggle current address updatind state"
            enabled: BBackend.coinManager.addressIndex >= 0
            checkable: true
            onCheckedChanged: {
                // TODO cannot test, not ui updating marker
                BBackend.coinManager.address.isUpdating = checked
            }
        }
        BMenuItem {
            text: "Populate wallets"
            onTriggered: {
                debugManager.makeWallets()
            }
        }
        BMenuItem {
            text: "Remove current wallet"
            enabled: BBackend.coinManager.addressIndex >= 0
            onTriggered: {
                // TODO test, actived for addressIndex, used as deleteCurrentWallet, check it
                BBackend.coinManager.deleteCurrentWallet()
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
            text: "Update"
            onTriggered: {
                // TODO ok, check actions
                debugManager.update()
            }
        }
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
        BMenu {
            title: "HTTP error simulation"
            BMenuItem {
                text: "404"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    BBackend.debugManager.simulateHTTPError(404)
                }
            }
            BMenuItem {
                text: "405"
                onTriggered: {
                    // TODO cannot test, not found ui visual updates
                    BBackend.debugManager.simulateHTTPError(405)
                }
            }
        }
    }
    BMenu {
        title: "Debug scenarios"
        BMenuItem {
            text: "Simulate MTX broadcasting"
            onTriggered: {
                // Error: name 'OP_RETURN' is not defined
                debugManager.simulateTxBroadcasting()
            }
        }
        BMenuItem {
            text: "SIGHUP simulation"
            onTriggered: {
                BBackend.debugManager.kill(1)
            }
        }
        BMenuItem {
            text: "SIGINT simulation"
            onTriggered: {
                BBackend.debugManager.kill(2)
            }
        }
        BMenuItem {
            text: "SIGQUIT simulation"
            onTriggered: {
                BBackend.debugManager.kill(3)
            }
        }
        BMenuItem {
            text: "Add dummy TX"
            onTriggered: {
                BBackend.coinManager.makeDummyTx()
            }
        }
        BMenuItem {
            text: "Simulate incoming transfer"
            onTriggered: {
                BBackend.coinManager.debugHistoryRequest()
            }
        }
        BMenuItem {
            text: "Look for HD chain"
            onTriggered: {
                BBackend.coinManager.lookForHD()
            }
        }
        BMenuItem {
            text: "Online mode"
            onTriggered: {
                BBackend.uiManager.online = !BBackend.uiManager.online
            }
        }
        BMenuItem {
            text: "Try old client version"
            onTriggered: {
                BBackend.debugManager.simulateClientVersion("0.9.1")
            }
        }
    }
    BMenu {
        title: "Mempool scenarios"
        BMenuItem {
            text: "Explore coin mempool"
            onTriggered: {
                BBackend.coinManager.retrieveCoinMempool()
            }
        }
        BMenuItem {
            text: "Monitor mempool"
            onTriggered: {
                BBackend.coinManager.monitorMempool()
            }
        }
        BMenuItem {
            text: "Fake coin tx status progress"
            enabled: BBackend.coinManager.coinIndex >= 0
            onTriggered: {
                BBackend.coinManager.fakeTxStatusProgress()
            }
        }
    }
}
