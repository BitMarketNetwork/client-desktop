# BitMarket Network Client Change Log

## 0.12.6 (09.07.2021)

* Fixed Linux Wayland support.
* Fixed generation of transactions for P2SH, P2WSH addresses.
* Python setuptools support.

## 0.12.5 (28.06.2021)

* Application quit confirmation.
* System Tray optimization.
* Dialogs optimization.
* Key Store optimization.
* Minor fixes.

## 0.12.4 (12.06.2021)

* Fixed calculation of the estimated transaction size on the "Send" page.
* The "Send" page now displays the estimated original size and virtual size of the transaction.
* Database: Private keys of HD addresses have been replaced on HD paths.
* Fixed iteration and generation of "broken" HD addresses (BIP-0044, BIP-0084). **The "broken" iteration is maintained until the summer of 2022.**

## 0.12.3 (22.05.2021)

* Fixed TLS connections on macOS.
* New algorithm for choosing UTXO`s for a transaction.
* New logger output format.
* New command line arguments: "--server-url", "--server-insecure".

## 0.12.2 (18.05.2021)

* UI: The configuration of visible coins now works correctly.
* Reimplemented BIP32 engine.

## 0.12.1 (12.05.2021)

* UI: Added server info to coin info page.
* Command line fixes:
  * description optimization
  * new argument "--configpath"
  * "--logfile" argument now support: stderr, stdout
  * argument "--debug_mode" renamed to "--debug"
  * if the application is not running in debug mode, the logging level is set to "info"
* Reimplemented network engine.
* Big code optimization.

## 0.12 (24.03.2021)

* QML: Addresses and History tabs with counter.
* Temporary application was changed to single-thread mode.
* Full support for EUR and USD currencies.
* Large code optimization.

## 0.11 (22.01.2021)

* New encryption format for private data (seed, phrase, databases). Not compatible with a previous version.
* Temporarily removed the СUI version of the application.
* Temporarily removed the wallet import, export, reset tools.
* Big code optimization/reimplementation

## 0.10.1 (31.12.2020)

* Fixes for public release.

## 0.10.0 (19.12.2020)

* Full reorganization.
* New UI.
* Partially code rewrite.

## 0.9.0

* Initial alpha revision.

## 0.9.1

* Critical DB fix.
* Small UI changes.

## 0.9.2

* A lot of crucial background improvements.
* New tests.
* A lot of UI changes.
* Russian and ukranian localization.
* Smart algorithm for source address selection for new outgoing transaction.
* Ability to select what unspents to use for outgoing transaction.
* Changes in master key generation from mnemonic phrase. If you lose your addresses or money because of this change you can move back to the previous revision (0.9.1).
* Rolling back transactions.

## 0.9.3

* Ability to view all coin transactions in one list (not only by address).
* UI skin change support.
* New 'Dark' skin.
* OS notification support.
* Tray icon and tray icon context menu support.
* Hide to tray function and new item in application settings to adjust this behavior.
* Mempool monitoring for new transactions.
* Many other fixes and new tests.
