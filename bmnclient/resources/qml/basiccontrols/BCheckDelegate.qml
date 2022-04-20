import QtQuick
import QtQuick.Controls

CheckDelegate {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }
    property alias toolTipItem: _toolTipLoader.sourceComponent

    // ICON {
    icon.width: _applicationStyle.icon.normalWidth
    icon.height: _applicationStyle.icon.normalHeight
    spacing: fontMetrics.averageCharacterWidth // BIconLabel comportable
    // } ICON

    highlighted: BListView.view ? BListView.isCurrentItem : false
    width: BListView.view ? BListView.view.viewWidth : (visible ? implicitWidth : 0)
    height: visible ? implicitHeight : 0
    display: BListView.view ? BListView.view.display : ItemDelegate.TextBesideIcon

    onImplicitWidthChanged: {
        if (BListView.view) {
            BListView.view.updateImplicitWidth()
        }
    }
    onVisibleChanged: {
        if (BListView.view) {
            BListView.view.updateImplicitWidth()
        }
    }
    onClicked: {
        if (BListView.view) {
            BListView.view.currentIndex = index
        }
    }

    Loader {
        id: _toolTipLoader
        active: _base.display === BItemDelegate.IconOnly
        sourceComponent: BToolTip {
            parent: _base
            text: _base.text
        }
    }

    indicator: BIconImage {
        x: _base.width - width - _base.rightPadding
        y: _base.topPadding + _base.availableHeight / 2 - height / 2
        sourceSize.width: _applicationStyle.icon.normalWidth / 2
        sourceSize.height: _applicationStyle.icon.normalHeight / 2
        visible: _base.checked
        color: Material.theme === Material.Dark ? Material.foreground : "transparent"
        source: _applicationManager.imagePath("check-solid.svg")
    }
}
