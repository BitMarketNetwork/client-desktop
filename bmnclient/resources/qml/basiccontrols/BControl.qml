import QtQuick 2.15
import QtQuick.Controls 2.15

Control {
    id: _base
    property FontMetrics fontMetrics: FontMetrics { font: _base.font }

    padding: 0
    spacing: 0
}
