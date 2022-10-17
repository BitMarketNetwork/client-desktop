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
            state: BBackend.configFolderListModel.count > 0 ? "Visible" : "Invisible"
            model: BBackend.configFolderListModel

            states: [
                State { name: "Visible" },
                State { name: "Invisible" }
            ]

            transitions: [
                Transition {
                    from: "Visible"
                    to: "Invisible"

                    BNumberAnimation {
                        target: _list
                        property: "BLayout.preferredWidth"
                        from: target.implicitWidth
                        to: 0
                    }
                }
            ]

            /*FolderListModel {
                folder: StandardPaths.writableLocation(StandardPaths.AppConfigLocation)
                showDirs: false
                sortField: FolderListModel.Time
                nameFilters: ["*.json"]
            }*/

            delegate: BItemDelegate {
                id: _item

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
                        id: _titleLabels
                        BLayout.fillWidth: true
                        BLabel {
                            BLayout.preferredWidth: _dateTimeLabel.width
                            font.bold: true
                            elide: BLabel.ElideRight
                            text: model.fileName
                        }
                        Item {
                            BLayout.fillWidth: true
                        }
                        BLabel {
                            id: _dateTimeLabel
                            BLayout.alignment: Qt.AlignRight
                            text: model.fileModified.toLocaleString(
                                Qt.locale(BBackend.settings.language.currentName),
                                Locale.ShortFormat)
                        }
                    }
                    // TODO: reimplement BContextMenuToolButton
                    // Error: Invalid write to global property "down"
                    BContextMenuToolButton {
                        BLayout.alignment: Qt.AlignRight
                        BLayout.rowSpan: 2
                        menu: BMenu {
                            BMenuItem {
                                text: qsTr("Remove")

                                onTriggered: {
                                    BBackend.configFolderListModel.onRemoveAccepted(model.filePath)
                                }
                            }
                        }
                    }
                    BLabel {
                        BLayout.preferredWidth: _titleLabels.width
                        elide: BLabel.ElideMiddle
                        text: model.filePath
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
