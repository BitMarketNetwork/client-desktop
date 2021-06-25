pragma Singleton

import QtQuick 2.15
import QtQuick.Controls.Material 2.15
import "../application"
import "../basiccontrols"

QtObject {
    // TODO move to bmnclient.cipher.password.PasswordStrength
    readonly property variant map: [
        [ false, "",                BCommon.ValidStatus.Unset  ],
        [ false, qsTr("Horrible"),  BCommon.ValidStatus.Reject ],
        [ false, qsTr("Weak"),      BCommon.ValidStatus.Reject ],
        [ false, qsTr("Medium"),    BCommon.ValidStatus.Reject ],
        [ true,  qsTr("Good"),      BCommon.ValidStatus.Accept ],
        [ true,  qsTr("Strong"),    BCommon.ValidStatus.Accept ],
        [ true,  qsTr("Paranoiac"), BCommon.ValidStatus.Accept ]
    ]

    function getMaxStringLength() {
        let length = 0
        for (let i = 0; i < map.length; ++i) {
            if(length < map[i][1].length) {
                length = map[i][1].length
            }
        }
        return length
    }

    function getIndex(password) {
        return password.length > 0 ? BBackend.calcPasswordStrength(password) : 0
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
