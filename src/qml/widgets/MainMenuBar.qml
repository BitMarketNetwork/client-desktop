import QtQuick 2.12
import QtQuick.Controls 2.12
import "../pages"
import "../controls"

MyMenuBar {


    signal quit()
    signal about()
    signal settings()
    signal exportAddress()
    signal newAddress()
    signal addWatchAddress()
    signal reload()
    signal restart()
    signal exportTransactions()
    signal clearTransactions()
    signal updateAddress()
    signal unixSignal(int signal)
    signal addDummytx()

    signal newMasterKey();
    signal inputSeedPhrase();
    signal welcomePage();
    signal showEmpty(bool show)

    property alias showEmptyValue: _show_empty.checked

    MyMenu {
        title: qsTr("Actions")


        MyMenuItem {
            id: _new_address
            text: qsTr("Create new address")
            onTriggered: newAddress()
        }

        MyMenuItem {
            id: _watch_only_address
            text: qsTr("Add watch-only address")
            onTriggered: addWatchAddress()
        }

        MyMenu{
            title: qsTr("Address")
            MyMenuItem{
                text: "Update"
                onTriggered: {
                    updateAddress()
                }
            }
            MyMenuItem{
                text: "Clear transactions"
                onTriggered: {
                    clearTransactions()
                }
            }
            MyMenuItem{
                text: "Export transactions"
                onTriggered: {
                    exportTransactions()
                }
            }
        }

        MenuSeparator{}

        MyMenuItem {
            text: qsTr("Export wallet")
            onTriggered: exportAddress()
        }


        MenuSeparator{ }

        MyMenuItem {
            text: qsTr("Exit")
            onTriggered: quit()
        }
    }

    MyMenu {
        title: qsTr("Tools")


        MyMenuItem {
            id: _show_empty
            text: qsTr("Show empty addresses")
            checkable: true
            onCheckedChanged: showEmpty(checked)
        }
        MyMenuItem {
            text: qsTr("Settings")

            onTriggered: settings()
        }
        MyMenuItem {
            text: qsTr("About")

            onTriggered: about()
        }
    }
/*
 will be removed on prod
 */
MyMenu {
    title: qsTr("Debug")
    MyMenuItem {
    text: qsTr("About debug")
    onTriggered: {
            msgbox("This debug menu will be removed later on production stage!")
        }
    }
    MyMenu{
        title: qsTr("UI tests")
        MyMenuItem{
            text: qsTr("Palette window")

            onTriggered: {
                pushPage("PalettePage.qml")
            }
        }

        MyMenuItem{
            text: qsTr("Notification test")

            onTriggered: {
                notify("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.");
            }
        }
        MyMenuItem{
            text: qsTr("Message box")

            onTriggered: {
                msgbox(qsTr("Testing message box appearance"))
            }
        }
        MyMenuItem{
            text: qsTr("Message box with choice")

            onTriggered: {
                msgbox(qsTr("Testing message box appearance"),true)
            }
        }

        MyMenuItem{
            text: qsTr("Watch address appending popup")
            onTriggered: {
                _watch.open()
            }
            AddWatchAddressPopup{
                id: _watch
            }
        }

        MyMenuItem{
            text: qsTr("Sending aprovement test")

            SendApprovePopup{
                id: _send_popup

                amount: "20.44"
                target: "33ymMNi7ioUUpoHiDPZun4PxK1CTtemVKm"
                fee:    "1.24"
                change: "3.56"
                unit:   "BTC"
                onSend: {
                    msgbox("Transaction about to send")
                }
            }

            onTriggered: {
               _send_popup.visible = true
            }
        }
        MyMenuItem{
            text: qsTr("Tx result popup test")
            onTriggered: {
                _tx_result.open()
            }

            TxResultPopup{
                id: _tx_result
                txHash: "f88fe4673ed5e304fbf4ff70bb994c356245cbb5bfb2f5da2c41c7dd50438d91"
                coinName: "btctest"
            }
        }

        MyMenuItem{
            text: qsTr("Spinner test")

            onTriggered: {
                wait(10)
            }
        }

        MyMenuItem{
            text: qsTr("Fee widget")

            MsgPopup{
                id: _fee_test
                FeeWidget{
                    anchors{
                        fill: parent
                        margins: 10
                    }
                }
            }

            onTriggered: {
                _fee_test.open()
            }
        }

        MyMenuItem{
            text: qsTr("Mnemo validation")

            onTriggered: {
                _mnemo_val.visible = true
            }
        }
        MyMenuItem{
            text: qsTr("Welcome window")

            onTriggered: {
                welcomePage()
            }
        }
        MyMenuItem{
            text: qsTr("Password set")

            onTriggered: {
                _psw_input.setMode = true
                _psw_input.visible = true
            }
        }
        MyMenuItem{
            text: qsTr("Password input")

            onTriggered: {
                _psw_input.setMode = false
                _psw_input.visible = true
            }
        }
    }
    MyMenu{
    title: qsTr("Key management")

    MyMenuItem {
        text: qsTr("Import backup copy")
        onTriggered: {
            CoinApi.keyMan.importWallet();
        }
    }
    MyMenuItem {
        text: qsTr("New master key")
        onTriggered: {
            newMasterKey();
        }
    }
    MyMenuItem {
        text: qsTr("Use existing seed phrase")
        onTriggered: {
            inputSeedPhrase();
        }
    }
    }
    MyMenu{
        title: qsTr("Wallet management")

        MyMenuItem {
            text: qsTr("New legacy address")
            onTriggered: {
                api.newAddress("",false)
            }
        }
        MyMenuItem {
            text: qsTr("New segwit address")
            onTriggered: {
                api.newAddress("",true)
            }
        }
        MyMenuItem {
            text: qsTr("UTXO list")
            onTriggered: {
                api.getAddressUnspentList()
                }
        }
        MyMenuItem {
            text: qsTr("Address details")
            enabled: api.addressIndex >=0

            onTriggered: {
                showAddressDetails(api.addressIndex)
            }
        }
        MyMenuItem {
            text: qsTr("Populate wallets")

            onTriggered: {
                debugManager.makeWallets()
            }
        }

        MyMenuItem {
            text: qsTr("Remove current wallet")
            enabled: api.addressIndex >=0

            onTriggered: {
                api.deleteCurrentWallet()
                }
        }
        MyMenuItem {
            text: qsTr("Clear all wallets")

            onTriggered: {
                api.clear()
                }
        }
    }
    MyMenu{
    title: qsTr("Polling")

    MyMenuItem {
        text: qsTr("Update")

        onTriggered: {
            debugManager.update()
        }
    }
    MyMenuItem {
        text: qsTr("Poll")

        onTriggered: {
            debugManager.poll()
        }
    }
    MyMenuItem {
        text: qsTr("Process tx list")

        onTriggered: {
            debugManager.reprocessTxList()
        }
    }
    MyMenuItem {
        text: qsTr("Stop polling")

        onTriggered: {
            debugManager.stopPolling()
        }
    }
    MyMenuItem {
        text: qsTr("Update fees")

        onTriggered: {
            debugManager.retrieveFee()
        }
    }
    }
    MyMenu{
        title: qsTr("Debug scenarios")

        MyMenuItem{
            text: qsTr("Simulate MTX broadcasting")

            onTriggered:{
                debugManager.simulateTxBroadcasting()
            }
        }
        MyMenuItem{
            text: qsTr("Reload QML")

            onTriggered:{
                reload()
            }
        }
        MyMenuItem{
            text: qsTr("Restart app")

            onTriggered:{
                restart()
            }
        }
        MyMenuItem{
            text: qsTr("SIGHUP simulation")

            onTriggered:{
                unixSignal(1)
            }
        }
        MyMenuItem{
            text: qsTr("SIGINT simulation")

            onTriggered:{
                unixSignal(2)
            }
        }
        MyMenuItem{
            text: qsTr("SIGQUIT simulation")

            onTriggered:{
                unixSignal(3)
            }
        }
        MyMenuItem{
            text: qsTr("Add dummy TX")

            onTriggered:{
                addDummytx()
            }
        }
        MyMenuItem{
            text: qsTr("Simulate incoming transfer")

            onTriggered:{
                CoinApi.coins.debugHistoryRequest()
            }
        }
        MyMenuItem{
            text: qsTr("Look for HD chain")

            onTriggered:{
                CoinApi.debuging.lookForHD()
            }
        }
        MyMenuItem{
            text: qsTr("Explore address mempool")

            onTriggered:{
                CoinApi.coins.retrieveAddressMempool()
            }
        }
        MyMenuItem{
            text: qsTr("Explore coin mempool")

            onTriggered:{
                CoinApi.coins.retrieveCoinMempool()
            }
        }
        MyMenuItem{
            text: qsTr("Online mode")

            onTriggered:{
                CoinApi.ui.online = !CoinApi.ui.online
            }
        }
    }
}
            InputPasswordPopup{
                id: _psw_input
            }
            MnemonicValidationPopup{
                id: _mnemo_val
            }
}
