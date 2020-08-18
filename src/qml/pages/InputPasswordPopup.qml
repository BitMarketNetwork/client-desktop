import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../js/constants.js" as Const

BasePopup {
    id: _base

    closable: false
    modal: true
    dim: true

    property bool setMode: true
    property int passwordStrength:  {
            _main.value? CoinApi.keyMan.validatePasswordStrength( _main.value ) : 0
        }


    readonly property variant strengthLevel:[
        "",
        qsTr("Horrible","Password strength level"),
        qsTr("Weak","Password strength level"),
        qsTr("Medium","Password strength level"),
        qsTr("Good","Password strength level"),
        qsTr("Strong","Password strength level"),
        qsTr("Paranoic","Password strength level"),
    ]

    readonly property int minimumStrength: 3


    ok: false
    canBeAccepted: {
        if(setMode){
            return !_switch.checked && isConfirmOk()
        }
        return isPasswordOk()
    }
    width: 650
    height: (setMode? 350 : 300) + 100


    function isPasswordOk(){
        return passwordStrength >= minimumStrength
    }
    function isConfirmOk(){
        return isPasswordOk() && _main.value.trim() === _confirm.value.trim()
    }




    onAccept: {
        if(!isPasswordOk()){
            return
        }

        if( setMode ){
            if(!CoinApi.keyMan.setNewPassword(_main.value)){
                _strength.text = qsTr("Critical error")
                return
            }
            setMode = false
            _main.value = ""
            _switch.checked = false
            return
        }
        if( !CoinApi.keyMan.testPassword(_main.value) ){
            _main.value = ""
            _strength.text = qsTr("Wrong password")
            _switch.checked = false
            return
        }
        if( !CoinApi.ui.dbValid){
            _db_warning.open()
            return
        }
        // strict order !!!
        _main.visible = false
        // first close it
        close()
        _main.value = "";
        CoinApi.keyMan.applyPassword(_main.value);
    }

    onReject: {
        Qt.quit()
    }

    onAboutToShow: {
        _main.forceActiveFocus()
    }

    Column{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10

        TitleText{
            id: _title
            text: setMode? qsTr("Set new password","Passwrod dialog") : qsTr("Input password","Passwrod dialog")
            width: parent.width
            bottomPadding: 20
        }

        Row{
            id: _main_row
            height: _main.height
            width: parent.width

            DetailInput{
                id: _main
                passwordInput: !_switch.checked
                name: qsTr("Password:","Password dialog")
                placeHolder: qsTr("Enter your password","Password dialog")
                width: parent.width - 140
                labelWidth: 200
                height: 40
                maxLength: 36
                focus: true
                failure: !isPasswordOk()
                enter: !setMode

                onValueChanged: {
                    if(!setMode){
                        _strength.text = ""
                    }
                }
            }
            Text {
                id: _strength
//                width: 100
                anchors{
                    verticalCenter: _main.verticalCenter

                }
                leftPadding: 10
                text: {
                    if(setMode){
                        return strengthLevel[passwordStrength]
                    }
                    return ""
                }
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                color: passwordStrength<minimumStrength?palette.brightText:palette.mid
//                visible: setMode
            }
            TxButton{
                id: _reset
                text: qsTr("Reset")
                height: Const.xemBtnHeight
                visible: !setMode && _strength.text.length === 0
                onClicked: {
                    _confirm_msg.open()
                }
                MsgPopup{
                    id: _confirm_msg
                    ok: false
                    text: qsTr("This will destroy all saved information and you can lose your money! Please make sure you remember the seed phrase. Reset?")
                    onAccept: {
                        close()
                            CoinApi.keyMan.removePassword();
                            _main.value = ""
                            _confirm.value = ""
                            setMode = true;
                    }
                }
                MsgPopup{
                    id: _db_warning
                    text: qsTr("Your current database version isn't supported in this application version (%1). You can reset your database either use old application version. \
                     Your master key won't be deleted. In case you reset databse you should wait some time to sinchornize data").arg(Qt.application.version)
                    ok: false
                    acceptText: qsTr("Reset")
                    onAccept: {
                        close()
                        CoinApi.ui.resetDB()
                        _base.close()
                    }
                    onReject: {
                        close()
                    }
                }
            }
        }
        DetailInput{
            id: _confirm
            passwordInput: true
            name: qsTr("Password confirmation:","Passwrod dialog")
            placeHolder: qsTr("Repeat your password here","Passwrod dialog")
            width: _main.width
            labelWidth: 200
//            visible: !_switch.checked
            enabled: !_switch.checked
            maxLength: 36
            height: 40
            failure: !isConfirmOk()
            visible: setMode
            enter: setMode
        }
        SwitchBox{
            id: _switch
            x: _main.inputX
            width: parent.width
            height: 40
            text: qsTr("Show password","Password dialog")
            onCheckedChanged: {
                _confirm.value = ""
            }
        }
    }

}
