import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"
import "../js/constants.js" as Constants


SendWidget {
    id: _base
    title: qsTr("Assets source:")
    height: 110

    property alias allAmount: _amount.amount
    property alias allFiat: _fiat.amount
    property alias sourceModel: _source.model
    property alias useAllAmount: _use_all.checked

    signal recalcSources()

    signal useAll(bool on)

    SourceComboBox{
        id: _source
       anchors{
            top: parent.top
            topMargin: 10
            right: parent.right
            margins: defMargin
            left: parent.left
            leftMargin: defLeftMargin
       }
       onActivated:{
           recalcSources()
       }
       enabled: false
       visible: false
    }

        SwitchBox{
            id: _use_all
            text: qsTr("Use the whole coin balance")

            anchors{
//                left: parent.left
//                leftMargin: defLeftMargin
                horizontalCenter: parent.horizontalCenter


                top: parent.top
                topMargin: defMargin
            }

            onCheckedChanged: {
                useAll(checked)
            }
        }

        LabelText{
            id: _amount_title
            anchors{
                left: parent.left
                leftMargin: defMargin
//                top:  _source.bottom
//                topMargin: 10
                bottomMargin: defMargin
                bottom: parent.bottom
            }
            text: qsTr("Amount available:")
        }
        MoneyCount{
            id: _amount
            anchors{
                left: _amount_title.right
                leftMargin: 10
//                top: _source.bottom
//                topMargin: 10
                verticalCenter: _amount_title.verticalCenter
            }
            unit: CoinApi.coins.unit
            width: 300
        }
        MoneyCount{
            id: _fiat
            anchors{
//                left: _amount.right
//                top: _amount.bottom
//                topMargin: 10
                margins: defMargin
//                bottom: _amount_title.bottom
                verticalCenter: _amount_title.verticalCenter
                right: parent.right
//                rightMargin: defMargin
            }
            unit: CoinApi.coins.currency
            width: 200
//            state: "right"
        }

}
