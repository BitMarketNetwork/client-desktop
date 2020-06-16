import QtQuick 2.12
import QtQuick.Controls 2.12

Rectangle {
    property bool blue: true
    property bool red: false

    height: 1
    radius: 2
    color: red? palette.brightText:blue? palette.link : palette.mid
}
