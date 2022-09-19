import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    title: qsTr("Select root key")
    width: parent.width / 2
    height: parent.height / 2

    signal keyStoreClicked(string key_store_id)
    signal generateAccepted
    signal restoreAccepted
    signal restoreBackupAccepted

    contentItem: BRowLayout {
        spacing: 5
        BListView {
            id: _list
            BLayout.fillWidth: true
            BLayout.fillHeight: true
            BLayout.preferredWidth: parent.width / 2
            visible: model.rowCount() > 0
            model: BBackend.keyStore

            delegate: BItemDelegate {
                id: _item
                height: implicitHeight

                contentItem: BGridLayout {
                    columns: 2
                    columnSpacing: 5

                    BIconImage {
                        BLayout.rowSpan: parent.columns
                        source: _applicationManager.imagePath("icon-wallet.svg")
                        sourceSize.width: _applicationStyle.icon.normalWidth
                        sourceSize.height: _applicationStyle.icon.normalHeight
                        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: model.name
                        font.bold: true
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: "no path"
                    }
                }

                onClicked: {
                    _base.keyStoreClicked(model.seed)
                }
            }
        }

        BColumnLayout {
            BLayout.fillWidth: true

            BButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                flat: true

                contentItem: BGridLayout {
                    columns: 2
                    columnSpacing: 5

                    BIconImage {
                        BLayout.rowSpan: parent.columns
                        source: _applicationManager.imagePath("file-circle-plus.svg")
                        sourceSize.width: _applicationStyle.icon.normalWidth
                        sourceSize.height: _applicationStyle.icon.normalHeight
                        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Generate new Root Key")
                        font.bold: true
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Create a new wallet to get started")
                    }
                }
                onClicked: {
                    _base.generateAccepted()
                }
            }
            BButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                flat: true

                contentItem: BGridLayout {
                    columns: 2
                    columnSpacing: 5

                    BIconImage {
                        BLayout.rowSpan: parent.columns
                        source: _applicationManager.imagePath("file-arrow-down.svg")
                        sourceSize.width: _applicationStyle.icon.normalWidth
                        sourceSize.height: _applicationStyle.icon.normalHeight
                        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Restore from Seed Phrase")
                        font.bold: true
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Enter Seed Phrase to access your wallet")
                    }
                }
                onClicked: {
                    _base.restoreAccepted()
                }
            }
            BButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                flat: true
                enabled: false

                contentItem: BGridLayout {
                    columns: 2
                    columnSpacing: 5

                    BIconImage {
                        BLayout.rowSpan: parent.columns
                        source: _applicationManager.imagePath("file-import.svg")
                        sourceSize.width: _applicationStyle.icon.normalWidth
                        sourceSize.height: _applicationStyle.icon.normalHeight
                        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Restore wallet from backup")
                        font.bold: true
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: qsTr("Open a local backup file")
                    }
                }
                onClicked: {
                    _base.restoreBackupAccepted()
                }
            }
        }
    }

    footer: BDialogButtonBox {
        BButton {
            BDialogButtonBox.buttonRole: BDialogButtonBox.RejectRole
            text: BCommon.button.cancelRole
        }
    }
}