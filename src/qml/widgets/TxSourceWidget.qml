import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../widgets"
import "../pages"
import "../js/constants.js" as Constants


SendWidget {
    id: _base
    title: qsTr("Asset source:","New transction window")
    height: 130

    property alias allAmount: _amount.amount
    property alias allFiat: _fiat.amount
    property alias sourceModel: _source_combo.model
    property alias sourceChoiseEnabled: _source_combo.enabled
    property alias useAllAmount: _use_all.checked
    property string currentAddress: ""

    signal recalcSources()

    signal useAll(bool on)


        SwitchBox{
            id: _use_all
            text: qsTr("Use the whole coin balance","New transction window")
            offText: qsTr("Use current address balance only","New transction window")
//            width: 270

            anchors{
                right: parent.right
                rightMargin: 20
                left: parent.left
                leftMargin: defLeftMargin
                top: parent.top
                topMargin: defMargin
            }

            onCheckedChanged: {
                useAll(checked)
            }

        }

        SubText{
            id: _source_title
            anchors{
                left: parent.left
                leftMargin: defLeftMargin
                top: _source_combo.top
//                topMargin: 10
//                bottom: _amount_title.top
//                margins: 10
            }
            text: qsTr("Select inputs:","New transaction window")
        }
        SourceComboBox{
            id: _source_combo
               anchors{
                    left: parent.left
                    leftMargin: defLeftMargin + 130
                    top: _use_all.bottom
                    topMargin: 20
                    right: parent.right
                    rightMargin: 20
               }
//               width: 200
               onClick: {
                   recalcSources()
               }
        }
        SubText{
            id: _amount_title
            anchors{
                left: parent.left
                leftMargin: defLeftMargin
                top:  _amount.top
            }
            text: qsTr("Available:","New transction window")

        }
        MoneyCount{
            id: _amount
            anchors{
//                left: _amount_title.right
//                leftMargin: 10
                top: _source_combo.bottom
                margins: defMargin
                left: _source_combo.left
                leftMargin: 0
//                right: _fiat.left
            }
            unit: CoinApi.coins.unit
            width: 100
        }
        MoneyCount{
            id: _fiat
            anchors{
                margins: defMargin
                verticalCenter: _amount.verticalCenter
                left: _amount.right
//                right: parent.right
            }
            unit: CoinApi.coins.currency
            width: 100
        }

}
