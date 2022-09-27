import QtQuick
import QtQuick.Controls.Material
//import Qt.labs.folderlistmodel
//import Qt.labs.platform
import "../application"
import "../basiccontrols"
import "../controls"

BDialog {
    id: _base
    title: qsTr("Select Root Key")
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
                    columns: 3
                    columnSpacing: 5

                    BIconImage {
                        BLayout.rowSpan: 2
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
                    BContextMenuToolButton {
                        BLayout.rowSpan: 2
                        menu: null
                        onClicked: {
                            // TODO 
                        }
                    }
                    BLabel {
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

            BKeyStoreDialogButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                title: qsTr("Generate new Root Key")
                details: qsTr("Create a new wallet to get started")
                imagePath: _applicationManager.imagePath("plus-solid.svg")

                onClicked: {
                    _base.generateAccepted()
                }
            }
            BKeyStoreDialogButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                title: qsTr("Restore from Seed Phrase")
                details: qsTr("Enter Seed Phrase to access your wallet")
                imagePath: _applicationManager.imagePath("rotate-right-solid.svg")

                onClicked: {
                    _base.restoreAccepted()
                }
            }
            BKeyStoreDialogButton {
                BLayout.fillWidth: true
                BLayout.fillHeight: true
                title: qsTr("Restore wallet from backup")
                details: qsTr("Open a local backup file")
                imagePath: _applicationManager.imagePath("rotate-right-solid.svg")
                enabled: false

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
