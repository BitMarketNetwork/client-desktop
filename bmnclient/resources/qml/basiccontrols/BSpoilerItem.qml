import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BColumnLayout {
    id: _base

    property alias contentItem: _loader.sourceComponent
    property alias headerItem: _header.sourceComponent
    property alias content: _loader.item
    property alias header: _header.item

    BRowLayout {
        BUnfoldToolButton {
            id: _unfoldBtn
        }
        Loader {
            id: _header
            BLayout.fillWidth: true
            BLayout.fillHeight: true
        }
    }
    Loader {
        id: _loader
        BLayout.fillWidth: true
        BLayout.minimumHeight: BLayout.preferredHeight
        BLayout.preferredHeight: 0
        BLayout.maximumHeight: BLayout.preferredHeight
        opacity: 0

        state: _unfoldBtn.checked ? "unfold" : "fold"

        states: [
            State { name: "fold" },
            State { name: "unfold" }
        ]

        transitions: [
            Transition {
                from: "fold"
                to: "unfold"

                SequentialAnimation {
                    BNumberAnimation {
                        id: heightAnimation
                        target: _loader
                        easing.type: Easing.InOutQuad
                        property: "BLayout.preferredHeight"
                        to: target.implicitHeight
                    }
                    BNumberAnimation {
                        id: opacityAnimation
                        target: _loader
                        property: "opacity"
                        to: 1
                    }
                }
            },
            Transition {
                from: "unfold"
                to: "fold"

                SequentialAnimation {
                    id: _animation
                    BNumberAnimation {
                        id: opacityAnimation1
                        target: _loader
                        property: "opacity"
                        to: 0
                    }
                    BNumberAnimation {
                        id: heightAnimation1
                        target: _loader
                        easing.type: Easing.InOutQuad
                        property: "BLayout.preferredHeight"
                        to: 0
                    }
                }
            }
        ]
    }
}
