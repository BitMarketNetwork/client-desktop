import QtQuick 2.12

QtObject {


    property string address: "892842380920c0eff"
    property string label: "some label"


    function toClipboard(){

    }

    function accept(){
        console.log("receiption accepted")
    }
}
