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
    signal removeAccepted(var path)

    property var file // FileModel

    contentItem: BGridLayout {
        id: _grid
        columns: 3
        columnSpacing: 5

        BIconImage {
            id: _icon
            Layout.rowSpan: 2
            source: _applicationManager.imagePath("icon-wallet.svg")
            sourceSize.width: _applicationStyle.icon.normalWidth
            sourceSize.height: _applicationStyle.icon.normalHeight
            color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        }
        BLabel {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignLeft
            Layout.maximumWidth: _grid.width - (_grid.columnSpacing * 2) - _icon.implicitWidth - _menuToolButton.implicitWidth
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
        id: _toolTip
        parent: _base
        width: _base.width * 2

        contentItem: BColumnLayout {
            BLabel {
                id: _fileName
                Layout.maximumWidth: _toolTip.availableWidth
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                wrapMode: Label.WrapAnywhere
                text: _base.file.name
            }
            BSeparator {
                Layout.fillWidth: true
            }
            BRowLayout {
                BLabel {
                    text: qsTr("Path")
                }
                BLabel {
                    Layout.maximumWidth: _toolTip.availableWidth - _toolTip.leftPadding - _toolTip.rightPadding
                    wrapMode: Label.WrapAnywhere
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
                _base.removeAccepted(_base.file.path)
            }
        }
    }

    onClicked: {
        _base.keyStoreClicked(_base.file.path)
    }
}
