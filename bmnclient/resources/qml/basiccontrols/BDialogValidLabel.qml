import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"

BLabel {
    id: _base

    enum Mode {
        Unset,
        Accept,
        Reject
    }
    property real maxAdvancedTextLength: 0
    property string advancedText: ""
    property int mode: BDialogValidLabel.Mode.Unset

    BLayout.alignment: _applicationStyle.dialogInputAlignment
    BLayout.preferredWidth: fontMetrics.averageCharacterWidth * (2 + maxAdvancedTextLength) * 1.5

    font.bold: true
    font.capitalization: Font.AllLowercase

    text: {
        let result
        switch (mode) {
        case BDialogValidLabel.Mode.Accept:
            result = BStandardText.symbol.acceptRole
            break
        case BDialogValidLabel.Mode.Reject:
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
        switch (mode) {
        case BDialogValidLabel.Mode.Accept:
            return Material.color(BStandardText.symbol.acceptRoleMaterialColor)
        case BDialogValidLabel.Mode.Reject:
            return Material.color(BStandardText.symbol.rejectRoleMaterialColor)
        default:
            return Material.foreground
        }
    }
}
