# JOK+
# Only standard imports, used by Makefile.
from pathlib import Path

MAINTAINER = "BitMarket Network"
MAINTAINER_DOMAIN = "bitmarket.network"
MAINTAINER_URL = "https://" + MAINTAINER_DOMAIN + "/"
NAME = "BitMarket Network Client"
SHORT_NAME = "bmn-client"
VERSION = (0, 11, 0)
VERSION_STRING = ".".join(map(str, VERSION))
ENCODING = "utf-8"
STRING_SEPARATOR = ":"

PYTHON_MINIMAL_VERSION = (3, 7, 0)

BASE_PATH = Path(__file__).parent.resolve()
RESOURCES_PATH = BASE_PATH / "resources"

TRANSLATIONS_PATH = ":/translations"

ICON_WINDOWS_FILE_PATH = RESOURCES_PATH / "images" / "icon-logo.ico"
ICON_DARWIN_FILE_PATH = RESOURCES_PATH / "images" / "icon-logo.icns"
ICON_LINUX_FILE_PATH = RESOURCES_PATH / "images" / "icon-logo.svg"
