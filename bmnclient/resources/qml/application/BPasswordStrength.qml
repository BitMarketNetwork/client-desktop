pragma Singleton

import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

QtObject {
    // sync with BBackend.rootKey.validatePasswordStrength()
    readonly property variant map: [
        [ false, "",               BDialogValidLabel.Mode.Unset  ],
        [ false, qsTr("Horrible"), BDialogValidLabel.Mode.Reject ],
        [ false, qsTr("Weak"),     BDialogValidLabel.Mode.Reject ],
        [ false, qsTr("Medium"),   BDialogValidLabel.Mode.Reject ],
        [ true,  qsTr("Good"),     BDialogValidLabel.Mode.Accept ],
        [ true,  qsTr("Strong"),   BDialogValidLabel.Mode.Accept ],
        [ true,  qsTr("Paranoic"), BDialogValidLabel.Mode.Accept ]
    ]

    function getMaxStringLength() {
        let length = 0
        for (let i = 0; i < map.length; i++) {
            if(length < map[i][1].length) {
                length = map[i][1].length
            }
        }
        return length
    }

    function getIndex(password) {
        return password.length > 0 ? BBackend.rootKey.validatePasswordStrength(password) : 0
    }

    function isAcceptable(index) {
        if(index < 0 || index >= map.length) {
            index = 0
        }
        return map[index][0]
    }

    function getString(index) {
        if(index < 0 || index >= map.length) {
            index = 0
        }
        return map[index][1]
    }

    function getValidMode(index) {
        if(index < 0 || index >= map.length) {
            index = 0
        }
        return map[index][2]
    }
}
