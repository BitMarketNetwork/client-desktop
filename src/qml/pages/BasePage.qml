import QtQuick 2.12
import QtQuick.Controls 2.12

import "../js/constants.js" as Constants
import "../js/functions.js" as Funcs
import "../api"
import "../controls"

Page {
    id: _body
    antialiasing: true

    readonly property int pageId: Constants.pageId.base
    readonly property QtObject api: CoinApi.coins
    readonly property int defaultMargin: 30

    signal wait(int timeout)


    function popPage(){
        _stackview.pop();
    }

    function toTop(){
        _stackview.pop(null);
    }

    function showPopup( path, props ){
        console.log(page , props)
    }

    function msgbox(text, choice){
        _msgbox.text = text;
        _msgbox.ok = !choice;
        _msgbox.open()
        return _msgbox;
    }

    function notify(text){
        _notification.text = text;
        _notification.open()
        return _notification;
    }

    background: Rectangle{
        color: palette.base
    }


    MsgPopup{
        id: _msgbox
    }

    BaseNotificationPopup{
        id: _notification
    }
}
