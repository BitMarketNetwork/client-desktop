import QtQuick 2.15

BScrollView {
    id: _base
    default property alias children: _layout.children
    property alias columns: _layout.columns
    property alias contentLayoutItem: _control.contentItem

    BColumnLayout {
        width: _base.width > implicitWidth ? _base.width : implicitWidth
        height: _base.height > implicitHeight ? _base.height : implicitHeight
        BControl {
            id: _control
            BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
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
