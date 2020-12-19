import "../basiccontrols"

BInfoValue {
    property BAmountObject amount: BAmountObject {}
    readonly property string stringFormat: "%1 %2 / %3 %4"
    text: stringFormat.arg(amount.valueHuman).arg(amount.unit).arg(amount.fiatValueHuman).arg(amount.fiatUnit)
}
