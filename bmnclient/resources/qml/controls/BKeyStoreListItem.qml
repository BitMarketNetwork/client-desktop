import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base

    display: BItemDelegate.IconOnly // for ToolTip

    signal keyStoreClicked(var path)
    signal renameAccepted(var path)

    property var file // FileModel

    contentItem: BGridLayout {
        columns: 3
        columnSpacing: 5

        BIconImage {
            Layout.fillWidth: true
            Layout.rowSpan: 2
            source: _applicationManager.imagePath("icon-wallet.svg")
            sourceSize.width: _applicationStyle.icon.normalWidth
            sourceSize.height: _applicationStyle.icon.normalHeight
            color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        }
        BLabel {
            font.bold: true
            elide: BLabel.ElideRight
            text: _base.file.name
        }
        BContextMenuToolButton {
            id: _menuToolButton
            Layout.alignment: Qt.AlignRight
            Layout.rowSpan: 2
            menu: null

            onClicked: {
                toggleMenu(_contextMenu)
            }
        }
        BLabel {
            Layout.fillWidth: true
            text: _base.file.mtimeHuman
        }
    }

    toolTipItem: BToolTip {
        parent: _base

        contentItem: BColumnLayout {
            BLabel {
                text: _base.file.name
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            }
            BSeparator {
                Layout.fillWidth: true
            }

            BRowLayout {
                BLabel {
                    text: qsTr("Path")
                }
                BLabel {
                    text: _base.file.path
                }
            }
        }
    }

    BMenu {
        id: _contextMenu
        BMenuItem {
            text: qsTr("Rename")

            onTriggered: {
                _base.renameAccepted(_base.file.path)
            }
        }
        BMenuItem {
            text: qsTr("Remove")

            onTriggered: {
                // TODO confirmation dialog
                BBackend.keyStoreList.onRemoveAccepted(_base.file.path)
            }
        }
    }

    onClicked: {
        _base.keyStoreClicked(_base.file.path)
    }
}
