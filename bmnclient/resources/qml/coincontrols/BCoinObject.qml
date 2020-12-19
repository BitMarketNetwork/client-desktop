import QtQuick 2.15

QtObject {
    property string name: "N/A"
    property int index: -1
    property string iconSource: ""

    property BAmountObject amount: BAmountObject {}

    property variant addressListModel: null
    property variant txListModel: null
}
