import QtQuick.Layouts

BItemDelegate {
    id: _base

    Layout.leftMargin: _applicationStyle.spacing * 0.25
    Layout.rightMargin: _applicationStyle.spacing * 0.25
    Layout.topMargin: _applicationStyle.spacing
    Layout.bottomMargin: _applicationStyle.spacing
    Layout.preferredWidth: Math.max(implicitWidth, implicitHeight)
    Layout.preferredHeight: Math.max(implicitWidth, implicitHeight)

    horizontalPadding: fontMetrics.averageCharacterWidth
    verticalPadding: fontMetrics.averageCharacterWidth

    display: BItemDelegate.IconOnly
    checkable: true
    autoExclusive: true
    down: checked
}
