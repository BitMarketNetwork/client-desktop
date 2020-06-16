import QtQuick 2.12

QtObject {
    property real amount: 0
    property real fee: 0
    property real change: 0
    property string traget: ""


    function send(){
        console.info("Sending transaction")
    }
}
