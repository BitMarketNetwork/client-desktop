import QtQuick 2.15
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
                BLayout.fillWidth: true
                BLayout.fillHeight: true
            }
            /*BLabel { // TODO
                BLayout.fillWidth: true
                visible: false // TODO _base.isUpdating
                text: qsTr("Updating...")
            }*/
        }
    }
}
