import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base

    signal keyStoreClicked(var path)
    signal renameAccepted(var path)

    property var file // FileModel

    contentItem: BGridLayout {
        columns: 3
        columnSpacing: 5

        BIconImage {
            Layout.rowSpan: 2
            source: _applicationManager.imagePath("icon-wallet.svg")
            sourceSize.width: _applicationStyle.icon.normalWidth
            sourceSize.height: _applicationStyle.icon.normalHeight
            color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        }
        BRowLayout {
            id: _titleLabels
            Layout.fillWidth: true
            BLabel {
                Layout.preferredWidth: _dateTimeLabel.width
                font.bold: true
                elide: BLabel.ElideRight
                text: _base.file.name
            }
            Item {
                Layout.fillWidth: true
            }
            BLabel {
                id: _dateTimeLabel
                Layout.alignment: Qt.AlignRight
                text: _base.file.mtimeHuman
            }
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
            Layout.preferredWidth: _titleLabels.width
            elide: BLabel.ElideMiddle
            text: _base.file.path
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
