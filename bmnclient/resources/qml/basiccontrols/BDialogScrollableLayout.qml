BScrollView {
    id: _scrollView
    default property alias content: _layout.children

    BControl {
        width: _scrollView.viewWidth
        height: _scrollView.viewHeight
        padding: _applicationStyle.padding

        contentItem: BColumnLayout {
            BDialogLayout {
                id: _layout
                BLayout.maximumWidth: implicitWidth
                BLayout.alignment: Qt.AlignTop | Qt.AlignHCenter
            }
        }
    }
}
