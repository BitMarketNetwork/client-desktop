import QtQuick 2.12

Text {
    font{
        bold: true
//        family: "Arial Narrow"
        family: "Arial"
        pixelSize: 16
    }
    color: enabled? palette.text : palette.mid
}
