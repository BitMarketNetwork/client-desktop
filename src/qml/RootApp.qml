import QtQuick 2.12
import QtQuick.Controls 2.12
import QtQuick.Window 2.12
import QtQuick.Controls.Material 2.12
import "pages"
import "widgets"
import "api"
import "js/constants.js" as Constants
import "js/functions.js" as Funcs

//import QtQuick.Controls.Material 2.12
//import Bmn 1.0

ApplicationWindow {
    id: _base

    title: 		Qt.application.name
    width: 		1090
    minimumWidth:	800
    maximumWidth: 	1800

    // font: Qt.font(CoinApi.settings.fontData)

    height: 	820
    minimumHeight: 700
    maximumHeight: 1280

        // Do not delete please !!!

    function reportSize(){
        console.log(`${width} x ${height}`)
    }
    onWidthChanged: reportSize()
    onHeightChanged: reportSize()


    visible: 	true

    Material.theme: 	Material.Dark
    Material.accent: 	Material.Brown
    Material.elevation: 10
    Material.primary: 	Material.BlueGrey

    /*
      rely on dynamic scoping for access
    */
    property ApplicationWindow appWindow: _base

    readonly property font simpleFont: Qt.font({
                                          family: "Arial",
                                          pixelSize: 14
                                      })


    // sugar
    readonly property QtObject api: CoinApi.coins

    function pushPage( fname , props = {}, replace = false ){
        const fpath = Qt.resolvedUrl("pages/" + fname);
        var mode = StackView.Transition
        if(replace && _stackview.currentItem.pageId > Constants.pageId.exchange){
            console.debug("Replacing page: " , fpath.slice(fpath.lastIndexOf("/") + 1));
            return _stackview.replace( _stackview.currentItem, fpath , props, mode);
        }
        if( CoinApi.debug ){
            console.debug("Pushing page: " , fpath.slice(fpath.lastIndexOf("/") + 1));
        }
        return _stackview.push(fpath , props, mode);
    }

    function copyAddress( addressIndex ){
        var address = null;
        if (CoinApi.dummy){
            address = api.addressModel[addressIndex]
        }
        else{
            address = api.coin.wallets[addressIndex]
        }
        CoinApi.ui.copyToClipboard(address.name)
    }

    function showAddressDetails( addressIndex ){
        var address = null;
        if (CoinApi.dummy){
            address = api.addressModel[addressIndex]
        }
        else{
            address = api.coin.wallets[addressIndex]
        }
        let mPage = pushPage("ExportAddressPage.qml",{
                  "wif" : address.to_wif,
                  "pub" : address.public_key,
                  "address" : address.name,
                  "label" : address.label,
                  "message" : address.message,
                  "created" : address.created,
         } );
         mPage.onClosed.connect(function(){
             address.label = mPage.label;
             address.save() // local slot!!?
         });
    }

    function removeAddress(addressIndex){
        api.removeAddress(addressIndex)
    }

    function actionClearTransactions( addresIndex ){
        api.clearTransactions(addresIndex)
    }

    function actionExportTransactions( addressIndex ){
        if( addressIndex >= 0 ){
            api.exportTransactions(addressIndex);
        }
        else{
            notify(qsTr("Select address to operate"))
        }
    }

    function actionUpdateAddress(addressIndex){
        if( addressIndex >= 0 ){
            api.updateAddress(addressIndex);
        }
        else{
            notify(qsTr("Select address to operate"))
        }
    }


    function msgbox(txt,choice){
        return _stackview.currentItem.msgbox(txt,choice);
    }

    function notify(txt){
        return _stackview.currentItem.notify(txt);
    }

    function wait(timeout){
        return _wait.wait(timeout);
    }

    function stopWaiting(){
        return _wait.stop()
    }

    function onMainPage(){
        return Constants.pageId.main === _stackview.currentItem.pageId
    }

    /*
        actions
    */
    function actionQuit(){
        Qt.quit()
    }
    function actionAbout(){
        pushPage("AboutPage.qml", {} ,true)
    }
    function actionSettings(){
        var page = pushPage("SettingsPage.qml", {} , true)
        // page.applyStyle.connect(actionReload)
        page.applyStyle.connect(actionRestart)
    }
    function actionExport(){
         CoinApi.keyMan.exportWallet();
    }
    function actionNewAddress(){
        if( !CoinApi.keyMan.hasMaster && !CoinApi.debug ){
            notify(qsTr("No master key detected"))
        }
        else if (api.coinIndex < 0){
            notify(qsTr("Select coin at first"))
        }
        else{
            _stackview.initialItem.newAddress(api.coinIndex)
        }
    }
    function actionAddWatchAddress(){
        if (api.coinIndex < 0 ){
            notify(qsTr("Select coin at first"))
        }
        else{
            _stackview.initialItem.addWatchOnlyAddress(api.coinIndex)
        }
    }
    function actionReload(){
        debuging.reload()
        _base.close()
        _wait.stop()
    }
    function actionRestart(){
        _restart.open()
    }
    function actionUnixSignal(sig){
        CoinApi.debuging.kill(sig)
    }
    function actionNewMasterkey(){
        if(onMainPage()){
            pushPage("MnemonicPage.qml",{ } );
        }
    }
    function actionInputSeed(){
        if(onMainPage()){
            pushPage("MnemonicPage.qml",{
                "pasteExisting": true,
            } );
        }
    }
    function actionWelcome(){
        _welcome.show()
    }
    function actionAddDummyTx(){
        CoinApi.coins.makeDummyTx()
    }
    function actionShowEmpty(show){
        api.showEmptyBalances = show;
    }



    background: Image {
        id: _bg_image
        smooth: true
        source: Funcs.loadImage("map_bg.png")
    }


    menuBar: MainMenuBar{
        id: _menu_bar
        showEmptyValue: CoinApi.coins.showEmptyBalances
        onAbout: 	actionAbout()
        onQuit: 	actionQuit()
        onSettings: actionSettings()
        onExportAddress: actionExport()
        onNewAddress: actionNewAddress()
        onReload: actionReload()
        onRestart: actionRestart()
        onUnixSignal: actionUnixSignal(signal)
        onAddWatchAddress: actionAddWatchAddress()
        onExportTransactions: actionExportTransactions(api.addressIndex)
        onClearTransactions: actionClearTransactions(api.addressIndex)
        onUpdateAddress: actionUpdateAddress(api.addressIndex)
        onInputSeedPhrase: actionInputSeed()
        onNewMasterKey: actionNewMasterkey()
        onWelcomePage: actionWelcome()
        onAddDummytx: actionAddDummyTx()
        onShowEmpty: actionShowEmpty(show)

        Component.onCompleted:{
            if(!CoinApi.debugMenu){
                _menu_bar.takeMenu(2)
            }
        }
    }

    header: MainToolBar{
        id: _tool_bar
//        width: 200
        showEmptyValue: CoinApi.coins.showEmptyBalances

        onAbout: 	actionAbout()
        onQuit: 	actionQuit()
        onSettings: actionSettings()
        onExportAddress: actionExport()
        onNewAddress: actionNewAddress()
        onAddWatchAddress: actionAddWatchAddress()
        onShowEmpty: actionShowEmpty(show)
    }

    footer: StatusBar{
        id: _status_bar
        online: CoinApi.ui.online
        message: CoinApi.ui.statusMessage
    }

    /*
    LeftPanel{
        id: _left_panel
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        onWalletClick: {
            console.log("page id: " + _stackview.pageId())
            if( _stackview.pageId() !== Constants.pageId.main ){
                console.log("Wallet mode")
                _stackview.pop(null)
            }
        }
        onExchangeClick: {
            console.log("page id: " + _stackview.pageId())
            if( _stackview.pageId() !== Constants.pageId.exchange ){
                console.log("Exchange mode")
                _stackview.pop(null)
                _stackview.push(_exchange_window)
            }
        }
    }
    /*/


    PageStack {
        id: _stackview
        initialItem: _main_window
        anchors{
            right:  parent.right
            top:  parent.top
            bottom:  parent.bottom
            // left:  _left_handle.right
            left:  parent.left
            /*/
            fill: parent
            */
        }
    }
 /*
    LeftDrawer{
        id: _left_panel
        visible: false
        y: _tool_bar.height + _menu_bar.height
        height: _base.height - y

        onWalletClick: {
            console.log("page id: " + _stackview.pageId())
            if( _stackview.pageId() !== Constants.pageId.main ){
                console.log("Wallet mode")
                _stackview.pop(null)
            }
        }
        onExchangeClick: {
            console.log("page id: " + _stackview.pageId())
            if( _stackview.pageId() !== Constants.pageId.exchange ){
                console.log("Exchange mode")
                _stackview.pop(null)
                _stackview.push(_exchange_window)
            }
        }
    }

    Rectangle{
        id: _left_handle
        anchors{
            top: parent.top
            bottom: parent.bottom
            left: parent.left
        }
        width: 6

        color: palette.mid
        radius: 1
        antialiasing: true

        border{
            width: 2
            color: palette.midlight
        }

        MouseArea{
            anchors{
                fill: parent
            }

            hoverEnabled: true

            onEntered: {
//                _left_panel.open()
            }
        }

    }
    */


    WaitPopup{
        id: _wait
        visible: false
        width: parent.width
        height: parent.height
    }

    Connections{
        target: CoinApi.ui
        onShowSpinner:{
            if(on){
                _base.wait();
            }else{
                _base.stopWaiting();
            }
        }
    }

    MainPage{
        id: _main_window
    }

    /**
      TODO: make it dynamic
    ExchangePage{
        id: _exchange_window
        visible: false
    }
    */

    /**
      TODO: make it dynamic
    */
    WelcomePopup{
        id: _welcome
        onNewMaster: {
            var mp = pushPage("MnemonicPage.qml",{ } );
            mp.back.connect(function(){
                _welcome.show()
            })
            _welcome.close();
        }
        onOldMaster: {
            var mp = pushPage("MnemonicPage.qml",{
                    "pasteExisting": true,
            } );
            mp.back.connect(function(){
                _welcome.show()
            })
            _welcome.close();
        }
        onFromBackup:{
            if(!CoinApi.keyMan.importWallet()){
                console.log("Import error")
                // open again strickly!!
            }else{
                _welcome.close();
            }
        }
        onReject: {
            Qt.quit()
        }
    }

    /**
      TODO: make it dynamic
    */
    InputPasswordPopup{
        id: _password_input
        setMode: !CoinApi.keyMan.hasPassword
    }

    BaseNotificationPopup{
        id: _restart
        text: qsTr("New settings will be applyed after next launch.")
    }

    Connections{
        target: CoinApi.ui
        onTermsAppliedChanged: {
            _welcome.checkTerms()
        }
    }
    Connections{
        target: CoinApi.keyMan
        onMnemoRequested: {
            _welcome.show()
        }
    }
    MsgPopup{
        id: _perms
        ok: false
        text: qsTr("<b>IMPORTANT NOTE:</b> The current application version is an alpha-version and does not warrant stable operation or safety of your finances. Please use this version with precautions for information only, as it is designed for demonstration purposes only.")
        canBeAccepted: false
        closable: false
        acceptText: qsTr("Accept")
        rejectText: qsTr("Decline")
        onAccept: {
            close()
            _password_input.open()
        }
        onReject: {
            Qt.quit()
        }
        onVisibleChanged:{
            if(visible){
                _activity_timer.running = true;
            }
        }
    }

    Timer{
        id: _activity_timer
        property int counter: 10
        interval: 1000
        onTriggered: {
            if(--counter  === 0 ){
                _perms.canBeAccepted = true
                _perms.acceptText = qsTr("Accept")
            }else{
                running = true
                _perms.acceptText = qsTr("Accept (%1)").arg(_activity_timer.counter)

            }
        }
    }

    Component.onCompleted: {
        _perms.open()
    }
}
