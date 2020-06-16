/*
    DON'T PUT IT IN RESOURCES

    it's dummy crap
*/
import QtQuick 2.12

Item {

    readonly property QtObject address: CoinApi.coins.address
    readonly property QtObject coin: CoinApi.coins.coin
    property real maxAmount: address.balance
    property real amount:  (maxAmount * 0.1).toFixed(coin.decimalFactor)
    property real fiatAmount: (amount * coin.rate).toFixed(2)
    property string receiverAddress: ""
    property bool canSend: receiverAddress.length > 0
    property bool receiverValid: receiverAddress.length > 0

    property real feeAmount: default_fee
    property real spbFactor:  0.5
    property real feeFiatAmount: (feeAmount * coin.rate).toFixed(2)
    property int  targetBlocks: (feeAmount * coin.rate).toFixed()
    property int  confirmTime: (feeAmount * 100 ).toFixed()

    property real changeAmount: 0.33
    property bool newAddressForChange: true
    property bool newAddressForLeftoverStatic: true
    property string changeAddress: "XXXXXXXXXXXX"
    property string spbAmount: "22"


    property bool substractFee: false

    readonly property string txHash : "909093092039029302904230482308heq"



    readonly property real balance: maxAmount
    readonly property real fiatBalance: (maxAmount * coin.rate).toFixed(coin.decimalFactor)


    readonly property real default_fee: 0.002
    readonly property real change_step: 100 / coin.rate
    readonly property int  decimal: CoinApi.coins.coin.decimalFactor
    readonly property variant targetList: [
            "3Jb9jJVRWYVdrf3p4w1hrxdCqHkeb9FDL2",
            "LLkYZVcYDZ4h87ZcX3aHWPCzHqFgBRyRGU",
        ]

    MutableTransaction{
        id: _transaction
        fee: feeAmount
        amount: amount
        change: changeAmount
    }

    signal fail(string error)
    signal sent()


    function setMax(){
       amount = maxAmount
    }


    function feeSlider(factor){
        feeAmount = (maxAmount * factor).toFixed(decimal);
    }

    /*
      validate then set
    */
    function setReceiverAddress(address){
        let valid =  address.length === 10;
        if(valid){
            receiverAddress = address;
        }else{
            receiverAddress = "";
        }

        return valid;
    }

    /*
      prepare output transaction

      we don't need anything. we have:
      - amount:
      - address:
      - feeAmount:

    */
    function prepareSend(){
        // unreal case .. but let it be
        if(!canSend){
            fail(qsTr("Source data for transaction is not valid"));
            return null;
        }


        if(false){
            fail("Some imagine error");
        }

        return true;
    }

    function send(){
        transaction.send();
        sent();
    }

    function cancel(){
        console.log("cancelling TX")
    }
}
