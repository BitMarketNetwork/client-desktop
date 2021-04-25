# JOK+++
# Only standard imports, used by Makefile.
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
    VERSION: Final = (0, 12, 0)
    VERSION_STRING: Final = ".".join(map(str, VERSION))
    ENCODING: Final = "utf-8"
    STRING_SEPARATOR: Final = ":"
    PYTHON_MINIMAL_VERSION: Final = (3, 7, 0)


class ProductPaths:
    BASE_PATH: Final = Path(__file__).parent.resolve()
    RESOURCES_PATH: Final = BASE_PATH / "resources"

    TRANSLATIONS_PATH: Final = ":/translations"

    ICON_WINDOWS_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.ico"
    ICON_DARWIN_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.icns"
    ICON_LINUX_FILE_PATH: Final = RESOURCES_PATH / "images" / "icon-logo.svg"


class Timer:
    NETWORK_TRANSFER_TIMEOUT: Final = 30 * 1000
    UPDATE_FIAT_CURRENCY_DELAY: Final = 60 * 1000
    UPDATE_SERVER_INFO_DELAY: Final = 60 * 1000
    UPDATE_COINS_INFO_DELAY: Final = 20 * 1000
    UPDATE_COINS_HD_DELAY: Final = 5 * 60 * 1000
