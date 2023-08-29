import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"
import "../dialogcontrols"
import "../controls"

BDialog {
    id: _base
    title: qsTr("Select Root Key")

    signal keyStoreClicked(var path)
    signal renameAccepted(var path)
    signal generateAccepted
    signal restoreAccepted
    signal restoreBackupAccepted

    contentItem: BDialogLayout {
        columns: 2

        Loader {
            id: _loader
            Layout.fillHeight: true
            Layout.fillWidth: true

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
                        property: "Layout.preferredWidth"
                        from: target.item.itemTemplateWidth
                        to: 0
                    }
                },
                Transition {
                    from: "Invisible"
                    to: "Visible"

                    BNumberAnimation {
                        target: _loader
                        property: "Layout.preferredWidth"
                        from: 0
                        to: target.item.itemTemplateWidth
                    }
                }
            ]

            sourceComponent: BKeyStoreListView {
                model: BBackend.keyStoreList

                delegate: BKeyStoreListItem {
                    file: modelObject

                    onKeyStoreClicked: (path) => {
                        _base.keyStoreClicked(path)
                    }
                    onRenameAccepted: (path) => {
                        _base.renameAccepted(path)
                    }
                }

                onCountChanged: {
                    _loader.state = BBackend.keyStoreList.rowCount() > 0 ? "Visible" : "Invisible"
                }
            }
        }

        BColumnLayout {
            Layout.fillWidth: true

            BKeyStoreDialogButton {
                title: qsTr("Generate new Root Key")
                details: qsTr("Create a new wallet to get started")
                imagePath: _applicationManager.imagePath("plus-solid.svg")

                onClicked: {
                    _base.generateAccepted()
                }
            }
            BKeyStoreDialogButton {
                title: qsTr("Restore from Seed Phrase")
                details: qsTr("Enter Seed Phrase to access your wallet")
                imagePath: _applicationManager.imagePath("rotate-right-solid.svg")

                onClicked: {
                    _base.restoreAccepted()
                }
            }
            BKeyStoreDialogButton {
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
