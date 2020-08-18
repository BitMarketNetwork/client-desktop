import QtQuick 2.12
import QtQuick.Controls 2.12
import "../controls"


Menu {
    id: _base
    topPadding: 2
    bottomPadding: 2

//    contentItem: Text{
//            text: _base.title
//            font.family: "Arial"
//            font.pixelSize: 12
//              opacity: _base.enabled ? 1.0 : 0.3
//              color:_base.highlighted ? palette.highlight : palette.text

//      horizontalAlignment: Text.AlignLeft
//      verticalAlignment: Text.AlignVCenter
//      elide: Text.ElideRight
//    }

//    background: Rectangle{
//        height: 40
//        width: 100
//    }
    delegate: MyMenuItem{}
}
