import QtQuick
import QtQuick.Layouts

import "../application"
import "../basiccontrols"

BControl {
    id: _base
    property alias model: _listView.model
    property real smallFontPointSize: _base.font.pointSize * _applicationStyle.fontPointSizeFactor.small

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

                delegate: BAddressTxItem {
                    tx: model
                }

                section.property: "state.timeHuman"
                section.criteria: ViewSection.FullString
                section.delegate: BLabel {
                    font.pointSize: _base.smallFontPointSize
                    text: section
                }
            }
            /*BLabel { // TODO
                BLayout.fillWidth: true
                visible: false // TODO _base.isUpdating
                text: qsTr("Updating...")
            }*/
        }
    }
}
