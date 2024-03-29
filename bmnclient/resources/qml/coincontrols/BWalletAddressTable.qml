import QtQuick
import QtQuick.Controls.Material
import Qt.labs.qmlmodels
import "../basiccontrols"

BControl {
    id: _base
    property var model // AddressList

    contentItem: Loader {
        sourceComponent: model.rowCountHuman > 0 ? _tableViewComponent : _emptyBoxComponent
    }

    Component {
        id: _emptyBoxComponent

        BEmptyBox {
            placeholderText: qsTr("Addresses not found.")
        }
    }

    Component {
        id: _tableViewComponent

        BColumnLayout {
            anchors.fill: parent

            BHorizontalHeaderView {
                id: _horizontalHeader
                BLayout.fillWidth: true
                syncView: _tableView
                visible: _tableView.rows > 0

                model: ObjectModel {
                    BControl {
                        BLabel {
                            anchors.centerIn: parent
                            text: qsTr("Address")
                        }
                    }
                    BControl {
                        BLabel {
                            anchors.centerIn: parent
                            text: qsTr("Label")
                        }
                    }
                    BControl {
                        BLabel {
                            anchors.centerIn: parent
                            text: qsTr("Balance")
                        }
                    }
                    BControl {
                        BLabel {
                            anchors.centerIn: parent
                            text: qsTr("Tx")
                        }
                    }
                }
                // TODO sorting controls
            }
            BAddressTableView {
                id: _tableView
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                model: _base.model
                columnWidth: [355, -1, 150, 65, 60]

                delegate: BAddressTableRow {
                    width: _tableView.columnWidthProvider(column)
                    address: model
                    amount: model.balance
                    contextMenu: _contextMenu

                    Rectangle { // col separator
                        anchors.right: parent.right
                        width: 1
                        height: parent.height
                        color: Material.dividerColor
                    }
                }
            }
        }
    }
}
