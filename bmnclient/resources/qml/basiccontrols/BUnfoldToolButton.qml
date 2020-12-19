import "../application"

BToolButton {
    id: _base

    checkable: true
    font.bold: true
    text: checked ? BStandardText.buttonText.foldControlRole : BStandardText.buttonText.unfoldControlRole
}
