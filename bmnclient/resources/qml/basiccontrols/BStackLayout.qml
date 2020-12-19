import QtQuick.Layouts 1.15

StackLayout {
    implicitHeight: currentIndex >= 0 ? children[currentIndex].implicitHeight : 0
    implicitWidth: currentIndex >= 0 ? children[currentIndex].implicitWidth : 0
}
