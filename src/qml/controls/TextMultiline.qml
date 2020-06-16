import QtQuick 2.12
import QtQuick.Controls 2.12
import "../js/constants.js" as Constants



TextArea {
    wrapMode: Text.Wrap
    textMargin: 10
    width: parent.width - 40
    font.pointSize: Constants.fontPointSize
    background: WidgetBG{

    }
}
