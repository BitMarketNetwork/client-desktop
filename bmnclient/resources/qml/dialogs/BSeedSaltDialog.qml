import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Particles 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    property alias salt: _manager.salt

    closePolicy: BDialog.NoAutoClose
    x: 0
    y: 0
    width: parent.width
    height: parent.height

    contentItem: MouseArea {
        id: _mouseArea
        hoverEnabled: true
        focus: true

        ColumnLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter

            BLabel {
                id: _label
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                Layout.fillWidth: true
                horizontalAlignment: BLabel.AlignHCenter
                wrapMode: BLabel.Wrap
                font.bold: true
                font.capitalization: Font.AllUppercase
                text: qsTr("Move cursor and press keyboard keys randomly to generate seed phrase")
            }
            BProgressBar {
                id: _progressBar
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                Layout.fillWidth: true
                to: _manager.stepCount
            }
            BButton {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                text: BStandardText.buttonText.cancelRole
                onClicked: {
                    _base.reject()
                }
            }
        }

        onPositionChanged: _manager.updateMouse(mouseX, mouseY)
        Keys.onPressed: _manager.updateKeyboard(event.key)

        ParticleSystem {
            id: _particleSystem
        }
        Emitter {
            system: _particleSystem

            emitRate: 200
            lifeSpan: 500
            size: _label.fontMetrics.xHeight * 2
            sizeVariation: _label.fontMetrics.xHeight

            x: _mouseArea.mouseX
            y: _mouseArea.mouseY

            velocity: PointDirection {
                xVariation: 1
                yVariation: 1
            }
            acceleration: PointDirection {
                xVariation: 2
                yVariation: 2
            }
            velocityFromMovement: 3
        }
        ImageParticle {
            system: _particleSystem
            source: "qrc:///particleresources/star.png"
            color: Material.color(Material.Yellow)
        }
    }

    onAboutToShow: {
        _progressBar.value = 0
    }

    // TODO read best practice
    QtObject {
        id: _manager

        property real salt: Date.now() * Math.random() // TODO use openssl
        property int mouseSalt: 0
        readonly property int stepCount: 500 + Math.random() * 501

        function updateMouse(x, y) {
            mouseSalt += (x * y) + (x + y)
            update(mouseSalt)
        }

        function updateKeyboard(key) {
            update((mouseSalt * key) + key)
        }

        function update(value) {
            if (value === 0) {
                return
            }

            let nextValue = salt * Math.sqrt(value) + _progressBar.value + 1
            if (nextValue !== 0) {
                if (!isFinite(nextValue)) {
                    salt *= 1e-100
                } else {
                    salt = nextValue
                }
                if (_progressBar.value++ >= _progressBar.to) {
                    _progressBar.value = 0
                    _base.accept()
                }
            }
            /*console.log(
                        "value = " + value
                        + ", nextValue = " + nextValue
                        + ", salt = " + salt)*/
        }
    }
}

