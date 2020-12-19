import QtQuick 2.15
import "../basiccontrols"

BControl {
    id: _base
    property alias model: _listView.model
    property alias delegate: _listView.delegate
    property alias templateDelegate: _itemTemplate.sourceComponent
    property int visibleItemCount: 0

    contentItem: BStackLayout {
        id: _stack
        currentIndex: _listView.count > 0 ? 1 : 0

        Loader {
            active: _stack.currentIndex === 0
            sourceComponent: BEmptyBox {
                placeholderText: qsTr("Addresses not found.")
            }
        }

        BListView {
            id: _listView
            implicitWidth: _base.visibleItemCount > 0 ? _itemTemplate.implicitWidth : 0
            implicitHeight: _base.visibleItemCount > 0 ? _itemTemplate.implicitHeight * _base.visibleItemCount : 0

            Loader {
                id: _itemTemplate
                visible: false
                active: _base.visibleItemCount > 0
            }
        }
    }
}
