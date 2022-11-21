import QtQuick
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"
import "../controls"

BDialog {
    id: _base
    title: qsTr("Select Root Key")

    signal keyStoreClicked(var path)
    signal renameAccepted(var path)
    signal generateAccepted
    signal restoreAccepted
    signal restoreBackupAccepted

    contentItem: BRowLayout {
        spacing: 5

        Loader {
            id: _loader
            BLayout.fillHeight: true
            BLayout.fillWidth: true

            state: BBackend.configFolderListModel.count > 0 ? "Visible" : "Invisible"
            states: [
                State { name: "Visible" },
                State { name: "Invisible" }
            ]
            transitions: [
                Transition {
                    from: "Visible"
                    to: "Invisible"

                    BNumberAnimation {
                        target: _loader
                        property: "BLayout.preferredWidth"
                        from: target.item.itemTemplateWidth
                        to: 0
                    }
                },
                Transition {
                    from: "Invisible"
                    to: "Visible"

                    BNumberAnimation {
                        target: _loader
                        property: "BLayout.preferredWidth"
                        from: 0
                        to: target.item.itemTemplateWidth
                    }
                }
            ]

            sourceComponent: BKeyStoreListView {
                model: BBackend.configFolderListModel

                delegate: BKeyStoreListItem {
                    fileName: model.fileName
                    fileModified: model.fileModified
                    filePath: model.filePath

                    onKeyStoreClicked: (path) => {
                        _base.keyStoreClicked(path)
                    }
                    onRenameAccepted: (path) => {
                        _base.renameAccepted(path)
                    }
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
