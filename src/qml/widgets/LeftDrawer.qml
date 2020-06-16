import QtQuick 2.12
import QtQuick.Controls 2.12

Drawer {
    id: _base
    edge: Qt.LeftEdge
    interactive: true
    width: _left_panel.width
    dragMargin: Qt.styleHints.startDragDistance

    signal walletClick()
    signal exchangeClick()

    LeftPanel{
        id: _left_panel

        anchors{
            fill: parent
        }

        onWalletClick: _base.walletClick()
        onExchangeClick: _base.exchangeClick()

        MouseArea{
            anchors.fill: parent
            id: _area
        }
    }

    Timer{
        id: _timer
        interval: 2000
        onTriggered:{
            if (!_area.hovered){
                _base.close()
            }
        }
    }

    onVisibleChanged:
    {
        if (visible){
            _timer.running = true;
        }
    }
}
