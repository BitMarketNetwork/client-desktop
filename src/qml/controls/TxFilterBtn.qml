import QtQuick 2.12
import QtQuick.Controls 2.12



TabButton{
    id: _base
    property bool notLast: false
    checkable: true
    autoExclusive: true
    visible: false
    signal select()

    background: Rectangle{
        radius: 5
        color: _base.checked? palette.highlight: _base.hovered? palette.midlight: palette.button
        /*
        gradient: ButtonGradient{
            colorOne: enabled? hovered? palette.mid: checked? palette.midlight: palette.button: palette.mid
            colorTwo: checked? palette.highlight: palette.mid
        }
        border{
            width: 1
            color: _base.checked?palette.button:"transparent"
        }
        */
    }

    contentItem: Label{
        color: checked? palette.highlightedText: palette.buttonText
        text: _base.text
        font{
            underline: hovered
        }
    }

    onClicked: {
        select()
    }
}
