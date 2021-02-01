import "../application"

BToolButton {
    id: _base

    checkable: true
    font.bold: true
    text: checked ? BStandardText.button.foldControlRole : BStandardText.button.unfoldControlRole
}
