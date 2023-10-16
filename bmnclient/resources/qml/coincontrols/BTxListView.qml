import QtQuick
import QtQuick.Layouts

import "../basiccontrols"

BControl {
    id: _base
    property alias model: _listView.model
    property alias delegate: _listView.delegate

    contentItem: BStackLayout {
        id: _stack
        currentIndex: _listView.count > 0 ? 1 : 0

        Loader {
            active: _stack.currentIndex === 0
            sourceComponent: BEmptyBox {
                placeholderText: qsTr("Transactions not found.")
            }
        }

        BColumnLayout {
            BListView {
                id: _listView
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            /*BLabel { // TODO
                BLayout.fillWidth: true
                visible: false // TODO _base.isUpdating
                text: qsTr("Updating...")
            }*/
        }
    }
}
