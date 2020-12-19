# http://dmgbuild.readthedocs.io
import os
from pathlib import Path

format = "UDBZ"
files = [
    str(Path(defines.get("DIST_SOURCE_DIR")).resolve())
]
symlinks = {
    "Applications": "/Applications"
}
# TODO create combined
# icon = str(Path(os.getenv("BMN_ICON_DARWIN_FILE_PATH")).resolve())
background = str(
    (Path(os.getenv("CONTRIB_PLATFORM_DIR")) / "background.png").resolve())
icon_locations = {
    Path(defines.get("DIST_SOURCE_DIR")).name: (180, 170),
    "Applications": (480, 170),
}
icon_size = 160
window_rect = ((300, 300), (660, 400))
sidebar_width = 0
default_view = "icon-view"
