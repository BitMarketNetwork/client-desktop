import QtQuick
import QtQuick.Controls

Label {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    elide: Label.ElideNone
    wrapMode: Label.NoWrap

    leftPadding: fontMetrics.averageCharacterWidth * 0.25
    rightPadding: fontMetrics.averageCharacterWidth * 0.25
    topPadding: fontMetrics.height * 0.1
    bottomPadding: fontMetrics.height * 0.1
}
