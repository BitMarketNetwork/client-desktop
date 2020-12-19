BControl {
    property alias placeholderText: _label.text
    padding: _applicationStyle.padding
    contentItem: BLabel {
        id: _label
        font.bold: true
        elide: BLabel.ElideRight
        horizontalAlignment: BLabel.AlignHCenter
    }
}
