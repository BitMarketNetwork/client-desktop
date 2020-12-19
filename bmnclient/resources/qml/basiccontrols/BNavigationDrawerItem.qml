BItemDelegate {
    id: _base

    BLayout.leftMargin: _applicationStyle.spacing * 0.25
    BLayout.rightMargin: _applicationStyle.spacing * 0.25
    BLayout.topMargin: _applicationStyle.spacing
    BLayout.bottomMargin: _applicationStyle.spacing
    BLayout.preferredWidth: Math.max(implicitWidth, implicitHeight)
    BLayout.preferredHeight: Math.max(implicitWidth, implicitHeight)

    horizontalPadding: fontMetrics.averageCharacterWidth
    verticalPadding: fontMetrics.averageCharacterWidth

    display: BItemDelegate.IconOnly
    checkable: true
    autoExclusive: true
    down: checked
}
