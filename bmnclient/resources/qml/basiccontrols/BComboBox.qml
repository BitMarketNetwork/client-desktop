import QtQuick.Controls 2.15
import QtQuick.Controls.Material 2.15

ComboBox {
    // BUG: Material
    // (parent or ancestor of Material): Binding loop detected for property "foreground"
    // Material.foreground: flat ? undefined : Material.primaryTextColor
    Material.foreground: undefined
}
