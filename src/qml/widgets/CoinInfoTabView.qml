import QtQuick 2.12
import QtQuick.Controls 2.12

import "../controls"
import "../js/constants.js" as Const


Base {
    id: _base


    property alias nameModel: _tab_model.model
    property alias coinName: _body.name
    property alias coinOnline: _body.online
    property alias coinVersionHuman: _body.versionHuman
    property alias coinVersionNum: _body.versionNum
    property alias coinHeight: _body.coinHeight

    signal selectCoin(int index)

//    height: 400
//    color: palette.base
//    radius: 10
    XemLine{
        anchors{
            top: _tabbar.bottom
            left: _base.left
        }
        width: _base.width
        id: _line
    }

    TabBar{
        id: _tabbar

//        spacing: 10
        height: Const.xemBtnHeight
        width: parent.width
        background: Base{ }

        anchors{
//            top: _header.bottom
        }

        Repeater{
            id: _tab_model
            TabHandler{
                id: _tbtn
                text: modelData
                width: Math.min(150, _base.width/ _tab_model.count)
                onClicked: {
                    selectCoin(model.index)
                }
            }
        }

    }

    CoinInfoTab{
        id: _body
        width: parent.width
//        height: 100
        anchors{
            top: _line.bottom
        }


    }

}
