import QtQuick 2.0

Item {

    property variant sourceModel: [
        {
            "unit" : "BTC",
            "fullName" : "Bitcoin",
            "icon" : "btc_icon.png"
        },
        {
            "unit" : "LTC",
            "fullName" : "Litecoin",
            "icon" : "ltc_icon.png"
        },
    ]
    property variant targetModel: [
        {
            "unit" : "BTC",
            "fullName" : "Bitcoin",
            "icon" : "btc_icon.png"
        },
        {
            "unit" : "LTC",
            "fullName" : "Litecoin",
            "icon" : "ltc_icon.png"
        },
    ]

    property int sourceIndex: -1
    property int targetIndex: -1
    property string sourceAmount: "0"
    property string targetAmount: "0"
    property string sourceFiatAmount: "0"
    property string targetFiatAmount: "0"

    property variant sourceCoin: null
    property variant targetCoin: null

    property int sourceDecimals: 2
    property int targetDecimals: 2

    property bool lockSource: false
    property bool lockTarget: false

    readonly property real ratio: 0.1

    function toHuman(val, dec = 2){
        return Number(val).toFixed(dec)
    }

    function increaseSource(){
        sourceAmount = toHuman(parseFloat(sourceAmount) + 10 , 0)
        console.log(sourceAmount)
    }

    function reduceSource(){
        sourceAmount = toHuman(Math.max(0,parseFloat(sourceAmount)*(1-ratio)) , 0)
    }
    function increaseTarget(){
        targetAmount = toHuman(parseFloat(targetAmount) + 10 , 0)
    }

    function reduceTarget(){
        targetAmount = toHuman(Math.max(0,parseFloat(targetAmount)*(1-ratio)) , 0)
    }

    function recalcTarget(){
        // dummy stuff
        var source = parseFloat(sourceAmount)
        targetAmount = toHuman(source * source)
        targetFiatAmount = toHuman(targetAmount * 9640.22)
    }
    function recalcSource(){
        // dummy stuff

        var target = parseFloat(targetAmount)
        sourceAmount = toHuman( Math.sqrt(target))
        sourceFiatAmount = toHuman(sourceAmount * 102.3)
    }

    onSourceAmountChanged: {
        lockSource = true
        recalcTarget()
        lockSource = false
    }
    onSourceIndexChanged: {
        sourceCoin = sourceModel[sourceIndex]
        if(lockSource){
            return;
        }
        // or target?
        lockSource = true
        recalcSource()
        lockSource = false
    }
    onTargetIndexChanged: {
        targetCoin = targetModel[targetIndex]
        lockTarget = true;
        recalcTarget()
        lockTarget = false;
    }
    onTargetAmountChanged: {
        if(lockTarget){
            return;
        }
        lockTarget = true;
        recalcSource()
        lockTarget = false;
    }
    Component.onCompleted: {
        sourceIndex = 0;
        targetIndex = 0;
    }
}
