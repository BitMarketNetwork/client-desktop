import logging
import sys
import pathlib
import re
try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

DOCS_FOLDER_NAME = "docs"
SYS_FOLDER_NAME = "sys"
"""
logging.basicConfig(
    format='[%(levelname)s] %(name)s[%(funcName)s]: %(message)s',
    # datefmt='%Y-%m-%d %H:%M:%S %z',
    style='%',
    level=logging.DEBUG,
    stream=sys.stdout)
"""


def local_path(folder: str) -> str:
    path = pathlib.Path(__file__).parent / folder
    if not path.exists():
        path.mkdir()
        with open(path / "__init__.py", "w") as _:
            pass
    return path


def docs_path() -> str:
    return local_path(DOCS_FOLDER_NAME)


def sys_path() -> str:
    return local_path(SYS_FOLDER_NAME)


def tr_items(prefix, suffix):
    "returns lang code, tr file and ts file"
    regex = re.compile(r"%s_(.+)_%s.txt" % (prefix, suffix))
    docs = f"{__name__}.{DOCS_FOLDER_NAME}"
    sysp = f"{__name__}.{SYS_FOLDER_NAME}"
    for res in pkg_resources.contents(docs):
        match = regex.match(res)
        if match:
            with pkg_resources.path(sysp, f"{prefix}_{match.group(1)}.ts") as path:
                ts = str(path)
            with pkg_resources.path(docs, res) as path:
                yield match.group(1), path, ts


def tr_codes():
    "returns only codes"
    regex = re.compile(r"qml_(.+).ts")
    sysp = f"{__name__}.{SYS_FOLDER_NAME}"
    for res in pkg_resources.contents(sysp):
        match = regex.match(res)
        if match:
            yield match.group(1)


def ts_files(prefix):
    "returns ts content"
    regex = re.compile(r"%s_(.+).ts" % prefix)
    sysp = f"{__name__}.{SYS_FOLDER_NAME}"
    for res in pkg_resources.contents(sysp):
        if regex.match(res):
            with pkg_resources.path(sysp, res) as path:
                yield path


# load from qrc
def binary_path_fail(prefix, suffix):
    # TODO: experienced some fialures with it// fix it later
    return f"://client/translation/{SYS_FOLDER_NAME}/{prefix}_{suffix}.qm"


def binary_path(prefix, suffix):
    try:
        sysp = f"{__name__}.{SYS_FOLDER_NAME}"
        with pkg_resources.path(sysp, f"{prefix.lower()}_{suffix.lower()}.qm") as path:
            return str(path)
    except FileNotFoundError as fe:
        raise RuntimeError(f"No such file: {fe}") from fe


def qml_binary_path(suffix):
    return binary_path("qml", suffix)


def py_binary_path(suffix):
    return binary_path("py", suffix)
