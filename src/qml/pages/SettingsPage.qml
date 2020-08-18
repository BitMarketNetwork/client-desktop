import QtQuick 2.12
import "../controls"
import "../widgets"
import "../api"
import "../js/constants.js" as Constants


BasePage {
    readonly property int pageId: Constants.pageId.settings

    signal applyStyle()


    TabWidget{
        anchors{
            top: parent.top
            bottom: parent.bottom
            left: parent.left
            topMargin: 30
            bottomMargin: 60
            right: parent.right
            rightMargin: parent.width * rightSpaceFactor
            margins: 10
        }

        id: _tabs
//        height: childrenRect.height


        GeneralSettingsTab{
            id: _general_tab
            title: qsTr("General", "Settings tab")

            languageModel: CoinApi.settings.languageModel
            currentLanguageIndex: CoinApi.settings.languageIndex
            onSelectLanguage: {
                CoinApi.settings.languageIndex = index
            }
            /*

            currencyModel: CoinApi.settings.currencyModel
            currentCurrencyIndex: CoinApi.settings.currencyIndex
            onSelectCurrency: {
                CoinApi.settings.currencyIndex = index
            }

            styleModel: CoinApi.settings.styleModel
            currentStyleIndex: CoinApi.settings.styleIndex
            onSelectStyle: {
                if (CoinApi.settings.styleIndex !== index){
                    applyStyle()
                    CoinApi.settings.styleIndex = index
                }
            }

            unitModel: CoinApi.settings.unitModel
            currentUnitIndex: CoinApi.settings.unitIndex
            onSelectUnit: {
                CoinApi.settings.unitIndex = index
            }
        */

        }
        CoinSettingsTab{
            id: _coins_tab
            title: qsTr("Coins", "Settings tab")
            model: api.staticCoinModel
        }
//        ExchangeSettingsTab{ id: _exchange_tab title: qsTr("Exchange", "Settings tab") }

        AdvancedSettingsTab{
            id: _advanced_tab

            title: qsTr("Advanced settings","Settings tab")


            rateSourceModel: CoinApi.settings.rateSourceModel
            currentRateSourceIndex: CoinApi.settings.rateSourceIndex

            onSelectRateSource: {
                CoinApi.settings.rateSourceIndex = index
            }

            useNewAddress: CoinApi.settings.newAddressFroLeftover

            onUseNewAddressChanged: {
                CoinApi.settings.newAddressFroLeftover = useNewAddress
            }

            onClearWallet:{
                popPage();
                CoinApi.keyMan.resetWallet()
            }
            onRestoreWallet: {
                popPage();
                CoinApi.keyMan.importWallet();
            }
        }
    }


    BigBlueButton{
        anchors{
//            horizontalCenter: _tabs.horizontalCenter
//            top: _tabs.bottom
//            topMargin: defaultMargin
            left: parent.left
            right: _tabs.right
            bottom: parent.bottom
            margins: 10

        }
        width: _tabs.width

        id: _btn_reject
        text: qsTr("Close")
        onClicked: {
        CoinApi.settings.accept();
        popPage()
        }
    }
}
