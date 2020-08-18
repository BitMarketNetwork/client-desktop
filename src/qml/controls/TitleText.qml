import QtQuick 2.12

Text {

    property bool sub: false

    color: palette.mid
    font{
        pixelSize: sub?20: ( activeHeight * .05 )
        family: "Helvetica"
    }

    elide: Text.ElideRight
}
