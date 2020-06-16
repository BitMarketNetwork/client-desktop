PY_DIR = client/client
QML_DIR = qml
TR_DIR = client/translation/sys


RESOURCES += resources.qrc

# doesn't work ?
QMAKEFEATURES += .
CONFIG += client

# workaround
include(features/client.prf)

SOURCES += \
    client/client/__init__.py \
    client/client/debug_manager.py \
    client/client/gcd.py \
    client/client/gcd_impl.py \
    client/client/key_manager.py \
    client/client/meta.py \
    client/client/server/__init__.py \
    client/client/server/net_cmd.py \
    client/client/server/network.py \
    client/client/server/network_impl.py \
    client/client/server/progress_view.py \
    client/client/server/server_error.py \
    client/client/server/thread.py \
    client/client/server/url_composer.py \
    client/client/ui/gui/__init__.py \
    client/client/ui/gui/api.py \
    client/client/ui/gui/app.py \
    client/client/ui/gui/coin_manager.py \
    client/client/ui/gui/exchange_manager.py \
    client/client/ui/gui/receive_manager.py \
    client/client/ui/gui/settings_manager.py \
    client/client/ui/gui/tx_controller.py \
    client/client/ui/gui/ui_manager.py \
    client/client/wallet/__init__.py \
    client/client/wallet/abs_coin.py \
    client/client/wallet/address.py \
    client/client/wallet/coin_info.py \
    client/client/wallet/coin_network.py \
    client/client/wallet/coins.py \
    client/client/wallet/constants.py \
    client/client/wallet/currency.py \
    client/client/wallet/database/__init__.py \
    client/client/wallet/database/database.py \
    client/client/wallet/database/db_wrapper.py \
    client/client/wallet/database/sqlite_impl.py \
    client/client/wallet/db_entry.py \
    client/client/wallet/fee_manager.py \
    client/client/wallet/hd.py \
    client/client/wallet/key.py \
    client/client/wallet/key_format.py \
    client/client/wallet/mnemonic.py \
    client/client/wallet/mtx_impl.py \
    client/client/wallet/mutable_tx.py \
    client/client/wallet/rate_source.py \
    client/client/wallet/rates.py \
    client/client/wallet/script.py \
    client/client/wallet/segwit_addr.py \
    client/client/wallet/serialization.py \
    client/client/wallet/thread.py \
    client/client/wallet/tx.py \
    client/client/wallet/util.py
