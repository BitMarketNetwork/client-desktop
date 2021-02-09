import QtQml 2.15

BScrollView {
    id: _base
    default property alias content: _layout.children

    BColumnLayout {
        Binding on implicitWidth {
            restoreMode: Binding.RestoreBindingOrValue
            when: _base.width > _control.implicitWidth
            value: _base.width
        }
        Binding on implicitHeight {
            restoreMode: Binding.RestoreBindingOrValue
            when: _base.height > _control.implicitHeight
            value: _base.height
        }
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
