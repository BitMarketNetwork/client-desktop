import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.12
import "../controls"
import "../api"
import "../js/functions.js" as Funcs
import "../js/constants.js" as Const


BasePage{
    id: _base

    readonly property int pageId: Const.pageId.mnemonic

    property bool pasteExisting: false
    property real extraSeed : _entropy_tool.entropy


    function generateSeed(){
        _entropy_tool.open()
    }

    signal back()

    EntropyWindow{
        id: _entropy_tool

        anchors.centerIn: Overlay.overlay

        onClosed: {
            // console.log(`extra seed tweak: ${extraSeed}`)
            _mnemo_text.textStatic = CoinApi.keyMan.getInitialPassphrase( extraSeed )
            }
    }

    MnemonicValidationPopup{
        id: _validator

        width: _mnemo_text.width
        height: 600
        // parent: Overlay.overlay

        x: Math.round((parent.width - width) / 2)
        y: 20

        onMatch: {
            console.log("Applying mnemo")
            _base.popPage()
        }
        onReject: {
            generateSeed()
        }
    }

    Component.onCompleted: {
        if(!pasteExisting){
            generateSeed()
        }
    }

    ColumnLayout{
        id: _column
        anchors{
            top: parent.top
            left: parent.left
            right: parent.right
            rightMargin: parent.width * rightSpaceFactor
            margins: 20
        }
        spacing: 20

        TitleText{
            text: pasteExisting?qsTr("Paste your phrase here","Send money result"): qsTr("New seed phrase","Master key window")
            Layout.fillHeight: true
            Layout.alignment: Layout.Left
        }

        MnemoInputField{
            id: _mnemo_text
            textStatic: (pasteExisting) ?"": CoinApi.keyMan.getInitialPassphrase(extraSeed)
            placeholder: pasteExisting?qsTr("Paste your seed phrase","Master key window"): ""
            readOnly: !pasteExisting && !CoinApi.debugSeed
            Layout.minimumHeight: 200
            Layout.fillWidth: true
        }
    }
    RowLayout{
        anchors{
            // bottom: parent.bottom
            // bottomMargin: 20
            top: _column.bottom
            topMargin: 40
            left: parent.left
            right: parent.horizontalCenter
            margins: 20
        }
        spacing: 20
        height: 40
        BigBlueButton{
            text: qsTr("Apply phrase","Master key window")
            enabled: {
                if(pasteExisting){
                    return CoinApi.keyMan.validateAlienSeed( _mnemo_text.textStatic )
                }

                return !_entropy_tool.visible && _mnemo_text.textStatic.length > 0
            }
            onClicked: {
                if(pasteExisting){
                    CoinApi.keyMan.generateMasterKey(
                        _mnemo_text.textStatic, CoinApi.debugSeed)
                    popPage()
                    // api.lookForHD()
                }
                else if(CoinApi.keyMan.preparePhrase(_mnemo_text.textStatic)){
                    _validator.open()
                    _mnemo_text.textStatic = ""
                }
            }
        }
        BigBlueButton{
            text: qsTr("Refresh","Master key window")
            visible: !pasteExisting
            onClicked: {
                generateSeed()
            }
        }
        BigBlueButton{
            text: qsTr("Back","Master key window")
            onClicked: {
                popPage()
                back()
            }
        }
    }
}
