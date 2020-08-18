import QtQuick 2.12
//import QtQuick.Controls 2.12
import "../api"
import "../controls"


BasePopup {
    id: _base
    closable: false
    ok: false

    width: 700

    signal newMaster()
    signal oldMaster()
    signal fromBackup()

    canBeAccepted: _terms.checked || CoinApi.ui.termsApplied

    Column{
        anchors{
            fill: parent
            margins: 10
        }
        spacing: 10

        MyRadioButton{
            id: _new_seed
            text: qsTr("Generate new master key","Master key window")
            checked: true
        }
        MyRadioButton{
            id: _old_seed
            text: qsTr("Enter old phrase","Master key window")
        }
        MyRadioButton{
            id: _backup
            text: qsTr("Restore from backup","Master key window")
        }
    }

    SwitchBox{
        id: _terms
        anchors{
            left: parent.left
            leftMargin: 110
            //right: parent.right
//            horizontalCenter: parent.horizontalCenter
            bottom: parent.bottom
            margins: 10
        }

        text: qsTr("I agree to <a href='terms_of_service'>terms of service</a> and <a href='privacy_policy'>privacy policy</a>")
        onGoLink: {
            console.log("Go to link:" + link)
            Qt.openUrlExternally("https:/google.com/" + link)
        }
    }

    onAccept: {
        if(_new_seed.checked){
            newMaster()
        }
        else if(_old_seed.checked){
            oldMaster()
        }else if(_backup.checked){
            fromBackup()
        }
        CoinApi.ui.termsApplied = true
    }

    function checkTerms() {
        if(CoinApi.ui.termsApplied){
            _terms.visible = false;
            canBeAccepted = true
        }
    }

    function show() {
        checkTerms()
        open()
    }

    Component.onCompleted: {
        checkTerms()
    }

}
