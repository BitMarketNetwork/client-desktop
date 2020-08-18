import QtQuick 2.12
import "../controls"

Tab {

    property alias languageModel: _locale.model
    property alias currentLanguageIndex: _locale.index

    property alias currencyModel: _currency.model
    property alias currentCurrencyIndex: _currency.index

    property alias styleModel: _style.model
    property alias currentStyleIndex: _style.index

    property alias unitModel: _unit.model
    property alias currentUnitIndex: _unit.index

    signal selectStyle(int index)
    signal selectLanguage(int index)
    signal selectCurrency(int index)
    signal selectUnit(int index)

    //color: "green"


        Column{
            spacing: 10
            anchors{
                fill: parent
            }
            SettingsComboBox{
                id: _locale
                role: "name"
                name: qsTr("Application language:","Settings item")
                width: parent.width
                onSelect: selectLanguage(index)
            }

            SettingsComboBox{
                id: _style
                role: "name"
                name: qsTr("Skin:","Settings item")
                width: parent.width
                onSelect: selectStyle(index)
                visible: false
            }

            SettingsComboBox{
                id: _unit
                role: "name"
                name: qsTr("Base unit:","Settings item")
                width: parent.width
                onSelect: selectUnit(index)
                visible: false
            }

            SettingsComboBox{
                id: _currency
                role: "name"
                name: qsTr("Fiat currency:","Settings item")
                width: parent.width
                onSelect: selectCurrency(index)
                visible: false
            }
        }

}
