import QtQuick.Controls 2.15

Menu {
    width: {
        let width = 0
        for (let i = 0; i < count; ++i) {
            let item = itemAt(i)
            width = Math.max(item.contentItem.implicitWidth + item.leftPadding + item.rightPadding, width)
        }
        return width
    }

    delegate: BMenuItem {}
}
