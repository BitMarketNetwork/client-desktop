import QtQuick
import Qt.labs.qmlmodels
import "../basiccontrols"

BTableView {
    id: _base
    BLayout.fillWidth: true
    BLayout.fillHeight: true

    //implicitWidth: _base.visibleItemCount > 0 ? _itemTemplate.item.implicitWidth : 0
    //implicitHeight: _base.visibleItemCount > 0 ? _itemTemplate.item.implicitHeight * _base.visibleItemCount : 0

    Loader {
        id: _itemTemplate
        visible: status == Loader.Ready
        //active: _base.visibleItemCount > 0
    }
}

/*BControl {
    id: _base
    property alias model: _listView.model
    property alias delegate: _listView.delegate
    property alias templateDelegate: _itemTemplate.sourceComponent
    property int visibleItemCount: 0

    contentItem: BStackLayout {
        id: _stack
        currentIndex: _listView.rows > 0 ? 1 : 0

        Loader {
            active: _stack.currentIndex === 0
            sourceComponent: BEmptyBox {
                placeholderText: qsTr("Addresses not found.")
            }
        }

        BColumnLayout {
            BHorizontalHeaderView {
                syncView: _listView

                model: ObjectModel {
                    id: itemModel
                    BLabel {
                        text: qsTr("Address")
                    }
                    BLabel {
                        text: qsTr("Label")
                    }
                    BLabel {
                        text: qsTr("Balance")
                    }
                    BLabel {
                        text: qsTr("Tx count")
                    }
                    BLabel {
                        text: qsTr("TODO")
                    }
                }
            }

            BTableView {
                id: _listView
                BLayout.fillWidth: true
                BLayout.fillHeight: true

                implicitWidth: _base.visibleItemCount > 0 ? _itemTemplate.item.implicitWidth : 0
                implicitHeight: _base.visibleItemCount > 0 ? _itemTemplate.item.implicitHeight * _base.visibleItemCount : 0

                Loader {
                    id: _itemTemplate
                    visible: false
                    active: _base.visibleItemCount > 0
                }
            }
        }
    }
}*/
