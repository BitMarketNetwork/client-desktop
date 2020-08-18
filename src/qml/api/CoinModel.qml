import QtQuick 2.12
import "../js/functions.js" as Funcs

ListModel{
    ListElement{
        fullName: "Bitcoin"
        netName: "Bitcoin"
        icon: "btc_icon.png"
        balance: 10222.12333
        fiatBalance: 933300444000
        rate: 7500
        unit: "BTC"
        defaultFee: 0.0001
        enabled: true
        visible: true
        test: false
        decimalFactor: 4
    }
    ListElement{
        fullName: "Bitcoin Test"
        netName: "Bitcoin Test"
        icon: "btc_icon.png"
        balance: 1022233312333
        fiatBalance: 933344
        rate: 7500
        unit: "BTC"
        defaultFee: 0.0001
        enabled: true
        visible: true
        test: true
        decimalFactor: 4
    }
    ListElement{
        fullName: "Litecoin"
        netName: "Litecoin"
        icon: "ltc_icon.png"
        balance: 234.1
        fiatBalance: 90044333333
        rate: 43
        unit: "LTC"
        defaultFee: 1
        enabled: true
        visible: true
        test: false
        decimalFactor: 2
    }
    ListElement{
        fullName: "Etherium"
        netName: "Etherium"
        icon: "eth_icon.png"
        balance: 1.34
        fiatBalance: 90044400000
        rate: 43
        unit: "ETH"
        defaultFee: 1
        enabled: true
        visible: true
        test: false
        decimalFactor: 0
    }
    ListElement{
        fullName: "BinanceCoin"
        icon: "bnb_icon.png"
        balance: 20.34
        fiatBalance: 9004.44
        unit: "BNB"
        defaultFee: 10
        enabled: false
        visible: true
        test: false
        decimalFactor: 0
    }
    ListElement{
        fullName: "XRP"
        icon: "xrp_icon.png"
        balance: 300453333333
        fiatBalance: 9004.44
        rate: 1
        unit: "XRP"
        defaultFee: 100
        enabled: false
        visible: true
        test: false
        decimalFactor: 0
    }
    ListElement{
        fullName: "Stellar"
        icon: "xlm_icon.png"
        balance: 990
        fiatBalance: 9004.44
        rate: 1
        unit: "XLM"
        currency: "USD"
        defaultFee: 100
        enabled: false
        visible: true
        test: false
        decimalFactor: 0
    }
    ListElement{
        fullName: "Tether"
        icon: "usdt_icon.png"
        balance: 11212211111
        fiatBalance: 9004.44
        rate: 1
        unit: "USDT"
        defaultFee: 10
        enabled: false
        visible: true
        test: false
        decimalFactor: 0
    }
    ListElement{
        fullName: "EOS"
        icon: "eos_icon.png"
        balance: 7000000
        fiatBalance: 9004.44
        rate: 1
        unit: "EOS"
        defaultFee: 10
        enabled: false
        visible: true
        test: false
        decimalFactor: 0
    }
}
