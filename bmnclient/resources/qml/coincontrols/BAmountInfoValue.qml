// JOK++
import "../application"
import "../basiccontrols"

BInfoValue {
    property var amount // AbstractAmountModel
    readonly property string stringFormat: "%1 %2 / %3 %4"
    text: {
        if (amount) {
            return stringFormat
                .arg(amount.valueHuman)
                .arg(amount.unit)
                .arg(amount.fiatValueHuman)
                .arg(amount.fiatUnit)
        } else {
            return stringFormat
                .arg(BStandardText.template.amount)
                .arg(BStandardText.template.unit)
                .arg(BStandardText.template.amount)
                .arg(BStandardText.template.unit)
        }
    }
}
