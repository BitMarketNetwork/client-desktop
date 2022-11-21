import QtQuick

import "../application"
import "../basiccontrols"

BListView {
    id: _base
    property int itemTemplateWidth: _itemTemplate.item.implicitWidth

    Loader {
        id: _itemTemplate
        visible: false

        sourceComponent: BKeyStoreListItem {
            fileName: BCommon.keyStoreItemTemplate.fileName
            fileModified: BCommon.keyStoreItemTemplate.fileModified
            filePath: BCommon.keyStoreItemTemplate.filePath
        }
    }
}
