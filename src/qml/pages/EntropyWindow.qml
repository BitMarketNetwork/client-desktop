import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"
import "../api"

Popup {
    id: _base

    property int entropy: Date.now()

    property int positionSalt: 1

    readonly property int maxEntropySteps: CoinApi.debug || CoinApi.debugSeed ? 100: 1000

    width: 600
    height: 600
    modal: true
    closePolicy: Popup.NoAutoClose

    function step( tweak ){
//        console.log(`SEED TWEAK ${tweak}`)
        if(tweak){
            entropy *= tweak;
            if(_progress.value ++ >= maxEntropySteps){
                close()
            }
        }
    }

    onVisibleChanged: {
        _progress.value = 0;
    }

    Rectangle{
        id: _body
        anchors{
            fill: parent
        }
        color: palette.midlight


        MouseArea{
            anchors{
                fill: _body
            }
            hoverEnabled: true
            onPositionChanged: {
                /*
                  TODO:
                  need to revise this algo thoroughly
                */
                 step((mouseX + 1)/( mouseY + 1));
                positionSalt = (mouseX + 1)*( mouseY + 1)
            }


        }

            Keys.onPressed: {
                step(event.key * positionSalt)
            }
            focus: true



        TitleText{
            id: _title
            anchors{
                centerIn: parent
            }
            text: qsTr("Move cursor randomly to generate seed phrase")
            font{
                pixelSize: 14
            }
        }
        ProgressBar{
            id: _progress
            anchors{
                top: _title.bottom
                left: parent.left
                right: parent.right
                margins: 20
            }
            from: 0
            to: maxEntropySteps

            background: Rectangle {
                      implicitWidth: 200
                      implicitHeight: 6
                      color: palette.base
                      radius: 3
                  }

                  contentItem: Item {
                      implicitWidth: 200
                      implicitHeight: 4

                      Rectangle {
                          width: _progress.visualPosition * parent.width
                          height: parent.height
                          radius: 2
                          color: palette.highlight
                      }
                  }
        }
    }
}
