import QtQuick.Controls
import QtQuick.Controls.Material

ComboBox {
    // BUG: Material
    // (parent or ancestor of Material): Binding loop detected for property "foreground"
    // Material.foreground: flat ? undefined : Material.primaryTextColor
    Material.foreground: undefined
}
