import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BLabel {
    id: _base

    property real maxAdvancedTextLength: 0
    property string advancedText: ""
    property int status: BCommon.ValidStatus.Unset

    Layout.alignment: _applicationStyle.dialogInputAlignment
    Layout.preferredWidth: fontMetrics.averageCharacterWidth * (2 + maxAdvancedTextLength) * 1.5

    font.bold: true
    font.capitalization: Font.AllLowercase

    text: {
        let result
        switch (status) {
        case BCommon.ValidStatus.Accept:
            result = BCommon.symbol.acceptRole
            break
        case BCommon.ValidStatus.Reject:
            result = BCommon.symbol.rejectRole
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
        case BCommon.ValidStatus.Accept:
            return Material.color(BCommon.symbol.acceptRoleMaterialColor)
        case BCommon.ValidStatus.Reject:
            return Material.color(BCommon.symbol.rejectRoleMaterialColor)
        default:
            return Material.foreground
        }
    }
}
