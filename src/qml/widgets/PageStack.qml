import QtQuick 2.12
import QtQuick.Controls 2.12
import "../pages"
import "../controls"

StackView {
    id: _base

    readonly property int animationDuration: 200

        function pageId(){
            console.log("Current on stack=>" + currentItem)
            return currentItem.pageId
        }

        background: Item { }


        pushEnter: Transition {
            YAnimator {
                from: _base.height
                to: 0
                duration: animationDuration
                easing.type: Easing.OutCubic
            }
        }

        pushExit: Transition {
            YAnimator {
                from: 0
                to: _base.height
                duration: animationDuration
                easing.type: Easing.OutCubic
            }
        }

        popEnter: Transition {
            YAnimator {
                from: -_base.height
                to: 0
                duration: animationDuration
                easing.type: Easing.OutCubic
            }
        }

        popExit: Transition {
            YAnimator {
                from: 0
                to: -_base.height
                duration: animationDuration
                easing.type: Easing.OutCubic
            }
        }
}
