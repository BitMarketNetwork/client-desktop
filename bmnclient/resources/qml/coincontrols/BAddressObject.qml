import QtQuick 2.15

QtObject {
    property BCoinObject coin: null

    property string name: "N/A"
    property string label: "N/A"
    property bool watchOnly: false
    property bool updating: false

    property BAmountObject amount: BAmountObject {}
}
