import QtQuick 2.15

QtObject {
    property string shortName: "N/A"
    property string fullName: "N/A"
    property string iconPath: ""

    property int index: -1

    property BAmountObject amount: BAmountObject {}

    property variant addressListModel: null
    property variant txListModel: null
}
