# Only standard imports, used by Makefile, setup.cfg.
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


class Product:
    MAINTAINER: Final = "BitMarket Network"
    MAINTAINER_DOMAIN: Final = "bitmarket.network"
    MAINTAINER_URL: Final = "https://" + MAINTAINER_DOMAIN + "/"
    NAME: Final = "BitMarket Network Client"
    SHORT_NAME: Final = "bmn-client"
    VERSION: Final = (0, 13, 1)
    VERSION_STRING: Final = ".".join(map(str, VERSION))
    ENCODING: Final = "utf-8"
    STRING_SEPARATOR: Final = ":"
    PYTHON_MINIMAL_VERSION: Final = (3, 7, 0)


class ProductPaths:
    BASE_PATH: Final = Path(__file__).parent.resolve()
    RESOURCES_PATH: Final = BASE_PATH / "resources"

    ICON_WINDOWS_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.ico"
    ICON_DARWIN_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.icns"
    ICON_LINUX_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.svg"

    CONFIG_FILE_NAME: Final = "config.json"
    DATABASE_FILE_NAME: Final = "wallet.db"

    QML_OFFLINE_STORAGE_PATH: Final = Path("qml") / "offline_storage"
    QML_CACHE_PATH: Final = Path("qml") / "cache"


class Timer:
    UI_MESSAGE_TIMEOUT: Final = 10 * 1000
    NETWORK_TRANSFER_TIMEOUT: Final = 30 * 1000
    UPDATE_FIAT_CURRENCY_DELAY: Final = 60 * 1000
    UPDATE_SERVER_INFO_DELAY: Final = 60 * 1000
    UPDATE_COINS_INFO_DELAY: Final = 20 * 1000
    UPDATE_COIN_HD_ADDRESS_LIST_DELAY: Final = 30 * 60 * 1000
    UPDATE_COIN_MEMPOOL_DELAY: Final = 15 * 1000


class Server:
    DEFAULT_URL_LIST: Final = (
        "https://d1.bitmarket.network:30110/",
    )


class Gui:
    QML_STYLE: Final = "Material"
    QML_FILE: Final = "main.qml"
    QML_CONTEXT_NAME: Final = "BBackend"
    DEFAULT_THEME_NAME: Final = "light"
    DEFAULT_FONT_POINT_SIZE: Final = 10


class Proxy:
    DEFAULT_PROXY_TYPE: Final = "HTTP"
