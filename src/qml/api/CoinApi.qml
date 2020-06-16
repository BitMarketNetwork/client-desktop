pragma Singleton
import QtQuick 2.12
//import Bmn 1.0

Item {
    id: _base
    visible: false


    /* =>* /

    readonly property bool dummy: true
    property QtObject coins: _mock
    property QtObject ui: _ui
    property QtObject keyMan: _key_manager
    property QtObject settings: _settings
    property QtObject exchange: _exchange
    property QtObject receive: _receive
    readonly property bool debug: true
    readonly property bool debugMenu: true
    readonly property bool debugSeed: true // hard to work without it
    /*
    Component.onCompleted: {
        console.log("available fonts:")
        for(var v in Qt.fontFamilies()){
            console.log(`${v} ==>> ${Qt.fontFamilies()[v]}`)
        }
    }
    */


    /* =>*/

    readonly property bool dummy: false
    property QtObject coins: coinManager
    property QtObject ui: uiManager
    property QtObject keyMan: keyManager
    property QtObject settings: settingsManager
    property QtObject exchange: exchangeManager
    property QtObject receive: receiveManager
    property QtObject debuging: debugManager
    readonly property bool debug: false
    readonly property bool debugMenu: false
    readonly property bool debugSeed: false // hard to work without it

    /* */

    SettingsController{
        id: _settings
    }

    ExchangeManager{
        id: _exchange
    }

    ReceiveManager{
        id: _receive
    }

    Item{
        id: _ui
        property bool online: false
        property bool termsApplied: false
        property string statusMessage: ""
        property string serverVersion: "XX.XX.XX"

        property variant coinInfoModel: [
                "Bitcoin",
                "Litecoin",
                "EOS",
        ]


        property int coinDaemonIndex: 0
        property variant coinDaemon: coinsModel[0]

        readonly property variant coinsModel: [
            {
                "name" : "Bitcoin",
                "versionHuman" : "Satoshi 15.1",
                "versionNum" : 12345,
                "height" 	: 400,
                "online"	: 1,
            },
            {
                "name" : "Litecoin",
                "versionHuman" : "LItecoinCore 0.1",
                "versionNum" : 92345,
                "height" 	: 300,
                "online"	: 1,
            },
            {
                "name" : "EOS",
                "versionHuman" : "EOS 5.1",
                "versionNum" : 16345,
                "height" 	: 500,
                "online"	: 0,
            },
        ]

        onCoinDaemonIndexChanged: {
            coinDaemon = coinsModel[coinDaemonIndex]
        }



        function copyToClipboard(text){
            console.log(`Clipboard simpulation: ${text}`)
        }


        signal showSpinner(bool on);

        Timer{
            id: _timer
            interval: 1000
            onTriggered: {
                _ui.showSpinner(false);
            }
        }

        Component.onCompleted: {
            _timer.running = true;
            coinInfoModel = coinsModel.map(function(c){ return c.name });
            coinDaemonIndex = 0;
        }
    }

    Item {
        id: _key_manager
        property bool hasMaster: true
        signal mnemoRequested()

        property string _phrase: ""
        property bool  hasPassword: true//Date.now() % 2

        function getInitialPassphrase(seed){
            return "Lorem ipsum dolor sit amet, consectetur adipiscing elit"
        }

        function generateMasterKey(seedphrase , debug){
            if( seedphrase === _phrase ){
                console.info("Master key generation from :" + seedphrase)
                return true;
            }
            return false;
        }

        function preparePhrase(phrase){
            _phrase = phrase
            return true
        }

        function resetWallet(){
            console.info("Reseting wallet")
        }
        function importWallet(){
            console.info("Importing wallet")
        }
        function exportWallet(){
            console.info("Exporting wallet")
        }
        // set new password
        function setNewPassword(pass){
            console.log(`new password setting simulation: ${pass}`)
        }
        // tests how safe new password is
        // returns int, the more the better
        function validatePasswordStrength(pass){
            return Number(1 + pass.length / 3).toFixed()
        }
        // tests old password ( password match)
        function testPassword(pass){
            return true;
            /*
            if( ! ( Date.now() % 2)){
                console.log(`password failure simulation`)
            }
            */
        }
        function applyPassword(pass){
            console.log(`apply psw : ${pass}`)
        }
        function removePassword(){
            console.log(`remove psw`)
        }

    }

    Item {
        id: _mock
        visible: false

        property int coinIndex: -1
        property  variant coinModel: []
        property  variant staticCoinModel: coinModel
        property  variant txModel: []
        property  variant addressModel: []
        property QtObject coin: null
        property int addressIndex: -1
        property QtObject address: null
        property bool showEmptyBalances: true
        property int txSortingOrder: 0
        readonly property string currency: "" // "USD"
        readonly property string unit: "BTC"

        // simulation
        readonly property int emptyCoin: 3;


        function exportWallet(file, pass){
            console.log("We are about to export wallet to file:" , file)
        }

        function importWallet(file, pass){
            console.log("We are about to import wallet from existing file:" , file)
        }

        function updateCoins(){
        }


        Component.onCompleted:{
            // modelData to work
            var i;
            for(i=0;i< _address_model.count;++i){
                addressModel.push(_address_model.get(i));
            }
            for(i=0;i< _tx_model.count;++i){
                txModel.push(_tx_model.get(i));
            }
            for( i=0;i< _coin_model.count;++i){
                var coin_ = _coin_model.get(i);
                if( i !== emptyCoin ){
                    coin_.wallets = addressModel;
                }else{
                    // simulate empty
                    coin_.wallets = [];
                }

                coinModel.push(coin_);
            }

        }

        function  getAddressModel(coin_idx) {
            // just loony simulation
            if (emptyCoin === coin_idx){
                return [];
            }

            return addressModel
        }

        function  walletsCount(coin_idx) {
            // just loony simulation
            return _address_model.count
        }

        function fiatAmount( amount , _coin = null ){
            let ccoin = _coin || _mock.coin
            return amount * ccoin.rate;
        }

        onCoinIndexChanged: {
            if(coinIndex >=0){
                _mock.coin = _coin_model.get(coinIndex)
                // dirty hack
                _mock.coin.wallets = [1]
                addressIndex = 0
            }else{
                _mock.coin = null
                addressIndex = -1
            }
            // to test
            _ui.online = _mock.coin !== null
        }

        onAddressIndexChanged: {
            if(addressIndex >=0){
                _mock.address = addressModel[addressIndex]
            }else{
                _mock.address = null
            }
        }

        function deleteWallet(wallet_index){
            addressModel.splice(wallet_index,1)
            coinIndex =-1
        }


        function clear(){
            addressModel = []
            coinIndex = -1
        }


        function makeAddress( index, label,  segwit){
            var add = {
                                  "name": segwit?"bc1q3gvshn60tpsmwnrj7f4p4hc2hmsld52pazada0":"1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX",
                                  "label": label,
                                  "balanceHuman": "0.03",
                                  "fiatBalance": "2390",
                                  "wif": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                                  "readOnly" : false,
                                  "useAsSource" : false,
                                  "isUpdating": false,
                              };
            console.log("new address created :" + add);
            // for signal emission
            var newModel = addressModel
            newModel.push(add)
            addressModel = newModel
        }
        function addWatchAddress( index, address, label){
            var add = {
                                  "name": address,
                                  "label": label,
                                  "balanceHuman": "0.03",
                                  "fiatBalance": "2390",
                                  "readOnly" : true,
                                  "useAsSource" : false,
                                  "isUpdating": false,
                              };
            console.log("new address appended :" + add);
            // for signal emission
            var newModel = addressModel
            newModel.push(add)
            addressModel = newModel
        }

        function clearTransactions(addressIndex){
            console.log(`clearing tx list ${addressIndex}`)
        }

        function exportTransactions( addressIndex ){
            console.log(`Exporting transactions from ${addressIndex}`)
        }

        CoinModel{
            id: _coin_model
        }

        AddressModel{
            id: _address_model
        }

        TxModel{
            id: _tx_model
        }
    }
}
