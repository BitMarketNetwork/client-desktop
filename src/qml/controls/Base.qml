import QtQuick 2.12
import "../api"

//Item {
Rectangle {
    color: CoinApi.debug && CoinApi.renderBg  ? tweakAlpha( renderColor , 0.5): "transparent"

    property color renderColor: "red"

    function tweakAlpha(color, alpha) {
        return Qt.hsla(color.hslHue, color.hslSaturation, color.hslLightness, alpha)
    }
}
