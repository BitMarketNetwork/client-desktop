BControl {
    id: _base
    default property alias children: _layout.children
    property alias columns: _layout.columns

    contentItem: BGridLayout {
        id: _layout
        property alias font: _base.font // for BInfoValue
        columns: 2
        columnSpacing: _applicationStyle.infoColumnSpacing
        rowSpacing: _applicationStyle.infoRowSpacing
    }
}
