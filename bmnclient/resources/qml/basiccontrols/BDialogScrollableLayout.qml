import QtQml 2.15

BScrollView {
    id: _base
    default property alias children: _defaultLayout.children
    property alias columns: _defaultLayout.columns
    property alias contentLayoutItem: _control.contentItem

    BColumnLayout {
        Binding on implicitWidth {
            restoreMode: Binding.RestoreBindingOrValue
            when: _control.forceUpdate && _base.width > _control.implicitWidth
            value: _base.width
        }
        Binding on implicitHeight {
            restoreMode: Binding.RestoreBindingOrValue
            when: _control.forceUpdate && _base.height > _control.implicitHeight
            value: _base.height
        }
        BControl {
            id: _control
            property bool forceUpdate: false // dirty force parent.Binding
            BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
            topPadding: _applicationStyle.padding
            leftPadding: _applicationStyle.padding
            bottomPadding: _applicationStyle.padding + _base.BScrollBar.vertical.width
            rightPadding: _applicationStyle.padding + _base.BScrollBar.horizontal.height
            contentItem: BDialogLayout {
                id: _defaultLayout
            }
            onVisibleChanged: {
                forceUpdate = visible
            }
            Component.onCompleted: {
                forceUpdate = true
            }
        }
    }
}
