import QtQuick
import QtQuick.Layouts

import "../basiccontrols"
import "../dialogcontrols"

BScrollView {
    id: _base
    default property alias children: _layout.children
    property alias columns: _layout.columns
    property alias contentLayoutItem: _control.contentItem
    property alias baseLayout: _baseLayout
    contentWidth: _base.availableWidth

    BColumnLayout {
        id: _baseLayout
        anchors.fill: parent

        BControl {
            id: _control
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
            topPadding: _applicationStyle.padding
            leftPadding: _applicationStyle.padding
            bottomPadding: _applicationStyle.padding + _base.BScrollBar.vertical.width
            rightPadding: _applicationStyle.padding + _base.BScrollBar.horizontal.height
            contentItem: BDialogLayout {
                id: _layout
            }
        }
    }
}
