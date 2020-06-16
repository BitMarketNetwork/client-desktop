import QtQuick 2.12

ListModel {
    ListElement{
        name: "3P3QsMVK89JBNqZQv5zMAKG8FK3kJM4rjt"
        label: "Main"
        message: "Some loooong message heeeeerrrrrrrrrrrrrrre"
        created: "08.02.2018 18:00"
        balance: 808080
        fiatBalance: "$89900"
        isUpdating: false
        readOnly: false
        to_wif: "some_wif"
        useAsSource: false
    }
    ListElement{
        name: "1F1tAaz5x1HUXrCNLbtMDqcw6o5GNn4xqX"
        // empty is possible
        label: ""
        message: "Some loooong message heeeeerrrrrrrrrrrrrrre"
        created: "08.12.2013 11:00"
        balance: 9045
        fiatBalance: "$34"
        isUpdating: false
        readOnly: true
        to_wif: "some_wif"
        useAsSource: false
    }
    ListElement{
        name: "3Jb9jJVRWYVdrf3p4w1hrxdCqHkeb9FDL2"
        label: "For testing bitcoins"
        message: ""
        created: "19.12.2020 11:00"
        balance: 909444444444
        fiatBalance: "$0.44"
        isUpdating: true
        readOnly: false
        to_wif: "some_wif"
        useAsSource: false
    }
    ListElement{
        name: "1QGrphsPEbxDFBAz66v1hJJfZXkwu4jcbF"
        label: "To bye car for my daddy and  buzzing on remains"
        message: "Some loooong message heeeeerrrrrrrrrrrrrrre"
        created: "08.12.2013 11:00"
        balance: 10000
        fiatBalance: "$340.44"
        isUpdating: false
        readOnly: false
        to_wif: "fff888f88f8f"
        useAsSource: false
    }
}
