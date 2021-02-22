import "../application"

BToolButton {
    id: _base

    checkable: true
    font.bold: true
    text: checked ? BCommon.button.foldControlRole : BCommon.button.unfoldControlRole
}
