import QtQuick 2.15

QtObject {
    property BCoinObject coin: null

    property string hash: "N/A"
    property int height: 0 // TODO human
    property int confirmationCount: 0 // TODO human
    property int status: 0

    property string timeHuman: "N/A"

    property BAmountObject amount: BAmountObject {}
    property BAmountObject feeAmount: BAmountObject {}

    property variant inputAddressListModel: null
    property variant outputAddressListModel: null
}
