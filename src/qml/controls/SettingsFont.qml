import QtQuick 2.12
import QtQuick.Dialogs 1.3
import "../api"
import "../js/functions.js" as Funcs

SettingsDisplayAction {
    id: _base

    FontDialog{
        id: _dialog
        title: qsTr("Select prefferable font")

        currentFont: appWindow.font
//        currentFont: Qt.font(CoinApi.settings.appFont)

        onAccepted: {
            _base.actionName = Funcs.fontDescription(font)
            _base.actionFont = font
            appWindow.font = font
            CoinApi.settings.fontData = Funcs.fontData(font)
        }

        onRejected: {

        }
    }

    Component.onCompleted: {
        _base.actionName = Funcs.fontDescription(_dialog.currentFont)
    }

    onEmitAction: {
        _dialog.open()
    }
}
