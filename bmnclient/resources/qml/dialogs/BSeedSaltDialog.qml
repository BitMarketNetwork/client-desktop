import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Material
import QtQuick.Particles

import "../application"
import "../basiccontrols"
import "../dialogcontrols"

BDialog {
    id: _base
    Material.roundedScale: Material.NotRounded

    property int stepCount
    signal updateSalt(string value)

    closePolicy: BDialog.NoAutoClose
    x: 0
    y: 0
    width: parent.width
    height: parent.height

    contentItem: MouseArea {
        id: _mouseArea
        hoverEnabled: true
        focus: true

        onPositionChanged: {
            _base.saltStep((mouseX * mouseY) + (mouseX + mouseY))
        }
        Keys.onPressed: {
            _base.saltStep(event.key)
        }

        BColumnLayout {
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
                text: qsTr("Move cursor and press keyboard keys randomly to generate Seed Phrase")
            }
            BProgressBar {
                id: _progressBar
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                Layout.fillWidth: true
                enabled: false
                to: _base.stepCount
            }
            BButton {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                text: BCommon.button.cancelRole
                onClicked: {
                    _base.reject()
                }
            }
        }

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
        _progressBar.enabled = true
    }

    onOpened: {
        _mouseArea.forceActiveFocus()
    }

    function saltStep(value) {
        if (_progressBar.enabled) {
            updateSalt("" + value)
            if (_progressBar.value++ >= _progressBar.to) {
                _progressBar.enabled = false
                _progressBar.value = 0
                Qt.callLater(accept) // exectute after all updateSalt()
            }
        }
    }
}
