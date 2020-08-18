/*
    DON'T PUT IT IN RESOURCES

    it's dummy crap
*/
import QtQuick 2.12

Item {

    property bool newAddressFroLeftover: true

    property variant fontData: {
        "family": "Tahoma",
        "pixelSize": 14,
    }

    property variant currencyModel: [
    ]
    property int currencyIndex: 0
    property QtObject currency: null

    property variant rateSourceModel: []
    property int rateSourceIndex: 0
    property QtObject rateSource: null

    property variant languageModel: [
        {name: "English"},
        {name: "Русский"},
        {name: "Français"},
    ]
    property int languageIndex: 0

    property variant styleModel: [
        {name: "Bmn"},
        {name: "Default"},
        {name: "Fusion"},
        {name: "Imagine"},
        {name: "Material"},
    ]
    property int styleIndex: 0
    property variant currentStyle: styleModel[styleIndex]

    property variant unitModel: [
        {name: "BTC" , factor: 8},
        {name: "mBtc", factor: 5},
        {name: "bits", factor: 2},
        {name: "sat", factor: 0},
    ]
    property int unitIndex: 0
    property variant baseUnit: unitModel[unitIndex]

    Component.onCompleted: {
        for(var i = 0 ; i < _currencies.count; ++i){
            currencyModel.push(_currencies.get(i))
        }
        currencyIndex = 0
        //
        for( i = 0 ; i < _rate_sources.count; ++i){
            rateSourceModel.push(_rate_sources.get(i))
        }
        rateSourceIndex = 0
    }

    onCurrencyIndexChanged: {
        currency = currencyModel[currencyIndex]
        console.log("New fiat:" , currency.name)
    }

    onRateSourceIndexChanged: {
        rateSource = rateSourceModel[rateSourceIndex]
        console.log("New rate source:", rateSource.name)
    }

    onStyleIndexChanged: {
    }

    function coinBalance(amount){
        if( 0 === baseUnit.factor){
            return amount
        }
        var val = amount / Math.pow(10, baseUnit.factor);
        var log =  Math.log10( val );
        return Number(val).toFixed( Math.max( 2-log, 0 )).toString()

    }

    function coinUnit(unit ){
        if (unit)
        {
            switch(baseUnit.factor){
            case 8:
                return unit;
            case 5:
                return "m" + unit[0] + unit.substr(1).toLowerCase();
            }
        }
        return baseUnit.name
    }

    function accept(){
        CoinApi.coins.updateCoins()
        console.log("use new addresses: " + newAddressFroLeftover)
        return true;
    }


    CurrencyModel{
        id: _currencies
    }

    RateSourceModel{
        id: _rate_sources
    }
}
