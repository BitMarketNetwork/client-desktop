import QtQuick
import QtQuick.Controls

Control {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    padding: 0
    spacing: 0
}
