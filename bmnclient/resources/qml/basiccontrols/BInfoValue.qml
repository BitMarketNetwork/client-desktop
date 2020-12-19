BTextField {
    BLayout.alignment: _applicationStyle.infoValueAlignment
    BLayout.minimumWidth: implicitWidth
    BLayout.fillWidth: true

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
