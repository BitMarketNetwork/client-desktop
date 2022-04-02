import QtQuick
import QtQuick.Controls.Material
import "../application"
import "../basiccontrols"

BColumnLayout {
    id: _base

    property string title
    property alias collapsibleItem: _detailsLoader.sourceComponent
    // TODO customize title item

    BRowLayout {
        BUnfoldToolButton {
            onCheckedChanged: {
                _detailsLoader.showControl(checked)
            }
        }
        BLabel {
            id: _titleLabel
            BLayout.fillWidth: true
            elide: BLabel.ElideMiddle
            text: _base.title
        }
    }
    Loader {
        id: _detailsLoader

        BLayout.fillWidth: true
        BLayout.minimumHeight: BLayout.preferredHeight
        BLayout.preferredHeight: 0
        BLayout.maximumHeight: BLayout.preferredHeight

        active: true

        onLoaded: {
            unfold()
        }

        NumberAnimation {
            id: _detailsAnimation
            target: _detailsLoader
            duration: _applicationStyle.animationDuration
            easing.type: Easing.InOutQuad
            property: "BLayout.preferredHeight"

            onFinished: {
                if (to === 0) {
                    _detailsLoader.active = false
                }
            }
        }

        function showControl(show) {
            _detailsAnimation.stop()
            if (show) {
                if (status === Loader.Ready) {
                    unfold()
                } else {
                    active = false // reset status to Loader.Null
                    active = true
                }
            } else {
                fold()
            }
        }

        function unfold() {
            _detailsAnimation.from = item.height
            _detailsAnimation.to = item.implicitHeight
            _detailsAnimation.restart()
        }

        function fold() {
            _detailsAnimation.from = item.height
            _detailsAnimation.to = 0
            _detailsAnimation.restart()
        }
    }

    Component.onCompleted: {
        _detailsLoader.showControl(false)
    }
}
