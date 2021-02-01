import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import QtQuick.Layouts 1.15
import QtQuick.Particles 2.15
import "../application"
import "../basiccontrols"

BDialog {
    id: _base
    readonly property int stepCount: 500 + Math.random() * 501

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
                enabled: false
                to: _base.stepCount
            }
            BButton {
                Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
                text: BStandardText.button.cancelRole
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
        _mouseArea.forceActiveFocus()
    }

    function saltStep(value) {
        if (_progressBar.enabled) {
            _base.updateSalt("" + value)
            if (_progressBar.value++ >= _progressBar.to) {
                _progressBar.enabled = false
                _progressBar.value = 0
                Qt.callLater(_base.accept) // exectute after all updateSalt()
            }
        }
    }
}
