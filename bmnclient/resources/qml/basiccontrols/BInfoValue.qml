import QtQuick.Layouts

BTextField {
    Layout.alignment: _applicationStyle.infoValueAlignment
    Layout.minimumWidth: implicitWidth
    Layout.fillWidth: true

    font.family:  parent.font.family
    font.pointSize: parent.font.pointSize
    font.bold: true

    readOnly: true
    background: null

    // SYNC: BLabel {
    leftPadding: fontMetrics.averageCharacterWidth * 0.25
    rightPadding: fontMetrics.averageCharacterWidth * 0.25
    topPadding: fontMetrics.height * 0.1
    bottomPadding: fontMetrics.height * 0.1
    // }

    // TODO append copy icon, copy on double click
}
