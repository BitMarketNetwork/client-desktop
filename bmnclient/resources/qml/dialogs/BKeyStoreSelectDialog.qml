import QtQuick
import QtQuick.Controls.Material
//import Qt.labs.folderlistmodel
//import Qt.labs.platform
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    title: qsTr("Select Root Key")
    width: parent.width / 2
    height: parent.height / 2

    signal keyStoreClicked(var path)
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
            model: BBackend.configFolderListModel

            /*FolderListModel {
                folder: StandardPaths.writableLocation(StandardPaths.AppConfigLocation)
                showDirs: false
                sortField: FolderListModel.Time
                nameFilters: ["*.json"]
            }*/

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
                    BRowLayout {
                        BLayout.fillWidth: true
                        BLabel {
                            BLayout.fillWidth: true
                            text: model.fileName
                            font.bold: true
                        }
                        BLabel {
                            BLayout.alignment: Qt.AlignRight
                            text: model.fileModified
                        }
                    }
                    BLabel {
                        BLayout.fillWidth: true
                        text: model.filePath
                        elide: BLabel.ElideRight
                    }
                }

                onClicked: {
                    _base.keyStoreClicked(model.filePath)
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
