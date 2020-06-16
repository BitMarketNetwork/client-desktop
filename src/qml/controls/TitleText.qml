import QtQuick 2.12

Text {

    property bool sub: false

    color: palette.mid
    font{
        pixelSize: sub?20:60
        family: "Helvetica"
    }

    elide: Text.ElideRight
}
