import QtQuick
import "../application"
import "../basiccontrols"

BPane {
    property string title: qsTr("Proxy")
    property string iconPath: _applicationManager.imagePath("icon-proxy.svg")

    contentItem: BDialogScrollableLayout {
        BDialogPromptLabel {
            text: qsTr("Application proxy type:")
        }
        BDialogInputComboBox {
            stateModel: BBackend.settings.proxy
            model: BCommon.proxyList
        }

        BDialogPromptLabel {
            text: qsTr("Host:")
        }
        BDialogInputTextField {
            id: _proxyHost
            text: BBackend.settings.proxy.hostProxy
            placeholderText: qsTr("username:password@host:port")
            onTextEdited: {
                BBackend.settings.proxy.hostProxy = text
            }
            onTextChanged: {
                BBackend.settings.proxy.hostProxy = text
            }

        }

        BDialogSeparator {}

        BDialogPromptLabel {
            text: qsTr("Enable proxy:")
        }
        BDialogInputSwitch {
            checked: BBackend.settings.proxy.enableProxy
            onCheckedChanged: {
                BBackend.settings.proxy.enableProxy = checked
            }
        }



    }
}
