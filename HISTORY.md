# BitMarket Network Client Change Log

## 0.11 (xx.01.2021)

* new encryption format for private data (seed, phrase, databases). Not
  compatible with a previous version.
* temporarily removed the СUI version of the application.
* temporarily removed the wallet import, export, reset tools.
* big code optimization/reimplementation

## 0.10.1 (31.12.2020)

* fixes for public release

## 0.10.0 (19.12.2020)

* full reorganization
* new UI
* partially code rewrite

## 0.9.0

* initial alpha revision

## 0.9.1

* critical DB fix
* small UI changes

## 0.9.2

* a lot of crucial background improvements
* new tests
* a lot of UI changes
* russian and ukranian localization
* smart algorithm for source address selection for new outgoing transaction
* ability to select what unspents to use for outgoing transaction
* changes in master key generation from mnemonic phrase. If you lose your 
  addresses or money because of this change you can move back to the previous 
  revision (0.9.1)
* rolling back transactions

## 0.9.3

* ability to view all coin transactions in one list ( not only by address )
* UI skin change support
* new 'Dark' skin
* OS notification support
* tray icon and tray icon context menu support
* hide to tray function and new item in application settings to adjust this behavior
* mempool monitoring for new transactions
* many other fixes and new tests
