import QtQuick 2.0
import QtQuick.Controls 2.12

Item {
    id: _base
    property bool input: true

    Label{
        id: _title
        text: _base.input?qsTr("Inputs"):qsTr("Outputs")
        color: palette.windowText
    }

}
