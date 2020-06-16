import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"
import "../js/constants.js" as Const

BasePopup {
    id: _base

    closable: false

    property bool setMode: true
    property int passwordStrength:  {
            _main.value? CoinApi.keyMan.validatePasswordStrength( _main.value ) : 0
        }


    readonly property variant strengthLevel:[
        "",
        qsTr("Horrible"),
        qsTr("Week"),
        qsTr("Middle"),
        qsTr("Good"),
        qsTr("Strong"),
        qsTr("Paranoic"),
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
        if( setMode ){
            CoinApi.keyMan.setNewPassword(_main.value);
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
        _main.visible = false
        CoinApi.keyMan.applyPassword(_main.value);
        _main.value = "";
        close()
    }

    onReject: {
        Qt.quit()
    }



    Column{
        anchors{
            fill: parent
            margins: 20
        }
        spacing: 10

        TitleText{
            id: _title
            text: setMode? qsTr("Setup new password") : qsTr("Input password")
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
                name: qsTr("Password:")
                placeHolder: qsTr("Input your password here")
                width: parent.width - 140
                labelWidth: 200
                height: 40
                maxLength: 36
                focus: true
                failure: !isPasswordOk()
                onValueChanged: {
                    if(!setMode){
                        _strength.text = ""
                    }
                }
            Keys.onEnterPressed: {
                accept()
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
                visible: !setMode
                onClicked: {
                    _confirm_msg.open()
                }
                MsgPopup{
                    id: _confirm_msg
                    ok: false
                    text: qsTr("It destroys all saved keys and transactions! Reset password?  ")
                    onAccept: {
                        close()
                        CoinApi.keyMan.removePassword();
                        _main.value = ""
                        _confirm.value = ""
                        setMode = true;
                    }
                }
            }
        }
        DetailInput{
            id: _confirm
            passwordInput: true
            name: qsTr("Password confirmation:")
            placeHolder: qsTr("Repeat your password here")
            width: _main.width
            labelWidth: 200
//            visible: !_switch.checked
            enabled: !_switch.checked
            maxLength: 36
            height: 40
            failure: !isConfirmOk()
            visible: setMode
        }
        SwitchBox{
            id: _switch
            x: _main.inputX
            width: parent.width
            height: 40
            text: qsTr("Show password")
            onCheckedChanged: {
                _confirm.value = ""
            }
        }
    }

}
