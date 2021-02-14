import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"

BLabel {
    id: _base

    enum Status {
        Unset,
        Accept,
        Reject
    }
    property real maxAdvancedTextLength: 0
    property string advancedText: ""
    property int status: BDialogValidLabel.Status.Unset

    BLayout.alignment: _applicationStyle.dialogInputAlignment
    BLayout.preferredWidth: fontMetrics.averageCharacterWidth * (2 + maxAdvancedTextLength) * 1.5

    font.bold: true
    font.capitalization: Font.AllLowercase

    text: {
        let result
        switch (status) {
        case BDialogValidLabel.Status.Accept:
            result = BStandardText.symbol.acceptRole
            break
        case BDialogValidLabel.Status.Reject:
            result = BStandardText.symbol.rejectRole
            break
        default:
            return ""
        }
        if (advancedText && advancedText.length > 0) {
            return result + " " + advancedText
        }
        return result
    }

    color: {
        switch (status) {
        case BDialogValidLabel.Status.Accept:
            return Material.color(BStandardText.symbol.acceptRoleMaterialColor)
        case BDialogValidLabel.Status.Reject:
            return Material.color(BStandardText.symbol.rejectRoleMaterialColor)
        default:
            return Material.foreground
        }
    }
}
