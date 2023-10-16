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
            file: BCommon.keyStoreItemTemplate
        }
    }
}
