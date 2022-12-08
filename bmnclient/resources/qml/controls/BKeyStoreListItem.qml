import QtQuick
import QtQuick.Controls.Material

import "../application"
import "../basiccontrols"

BItemDelegate {
    id: _base

    signal keyStoreClicked(var path)
    signal renameAccepted(var path)

    property string fileName
    property var fileModified
    property string filePath

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
                text: _base.fileName
            }
            Item {
                BLayout.fillWidth: true
            }
            BLabel {
                id: _dateTimeLabel
                BLayout.alignment: Qt.AlignRight
                text: _base.fileModified.toLocaleString(
                    Qt.locale(BBackend.settings.language.currentName),
                    Locale.ShortFormat)
            }
        }
        BContextMenuToolButton {
            id: _menuToolButton
            BLayout.alignment: Qt.AlignRight
            BLayout.rowSpan: 2
            menu: null

            onClicked: {
                _contextMenu.popup()
            }
        }
        BLabel {
            BLayout.preferredWidth: _titleLabels.width
            elide: BLabel.ElideMiddle
            text: _base.filePath
        }
    }
    BMenu {
        id: _contextMenu
        BMenuItem {
            text: qsTr("Rename")

            onTriggered: {
                _base.renameAccepted(_base.filePath)
            }
        }
        BMenuItem {
            text: qsTr("Remove")

            onTriggered: {
                BBackend.configFolderListModel.onRemoveAccepted(_base.filePath)
            }
        }
    }

    onClicked: {
        _base.keyStoreClicked(_base.filePath)
    }
}
