// JOK++
import "../basiccontrols"

BInfoValue {
    property var amount // AbstractAmountModel
    text: "%1 %2 / %3 %4"
            .arg(amount.valueHuman)
            .arg(amount.unit)
            .arg(amount.fiatValueHuman)
            .arg(amount.fiatUnit)
}
