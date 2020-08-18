
import logging
import sys
import re
import xml.etree.ElementTree as ET
from . import tr_codes
from . import ts_files
from . import docs_path
from . import tr_items

log = logging.getLogger(__name__)


def run():
    """
    makes qml_src.txt and py_src.txt what expect to be translated in any cloud translating service to
    many qml_{lang code}_tr.txt and py_{lang code}_tr.txt files according to the languages quantity

    attention! new sources (a couple of them) are generated everytime
    """
    make_source("qml")
    make_source("py")

    # update_ts("qml")
    # update_ts("py")


def src_path(prefix):
    assert prefix in ("qml", "py")
    return docs_path() / f"{prefix}_src.txt"


def make_source(prefix):
    """
    makes ONE src file
    """
    try:
        ts = next(ts_files(prefix))
        with open(ts, encoding="utf-8") as fh:
            root = ET.parse(fh).getroot()
    except ET.ParseError as per:
        raise SystemError(f"{per} at {ts}") from per

    def line():
        for cxt in root:
            yield f"##{cxt.find('name').text}\n"

            for src in cxt.findall(".message/source"):
                yield f"{src.text}\n"
            yield "####\n\n"
    with src_path(prefix).open("w") as fh:
        # fh.writelines( f"{src.text}\n" for src in tree.getroot().findall(".context/message/source"))
        fh.writelines(iter(line()))
        log.info(f"new translation source for {prefix} is ready")


class MismatchError(RuntimeError):

    def __init__(self, file, idx, src, tr):
        super().__init__(
            f"File mismatch in {file} at line #{idx}. '{src}' != '{tr}'")


def update_ts(prefix):
    """
    Updates all *.ts files accroding to qml_{lang code}.txt and py_{lang code}.txt sources
    """
    comment = re.compile(r"##(?:##)?\s?(\w+)?")
    db_ = None

    def do_ts(name, ts):
        try:
            with open(ts, encoding="utf8") as fh:
                dom = ET.parse(fh)
        except ET.ParseError as per:
            raise SystemError(f"{per} at {ts}") from per
        for message in dom.getroot().iterfind("./context/message"):
            source = message.find("source")
            tr = message.find("translation")
            tr.text = db_.get(source.text.strip())
        dom.write(ts)
                # don't break here !!! might be more source with the same text
    for name, final, ts in tr_items(prefix, "tr"):
        log.debug(f"{name}= {final}")
        db_ = db.Db(name)
        with src_path(prefix).open("r",encoding="utf8") as srch:
            with open(final, "r",encoding="utf8") as trh:
                for i, (src, tr) in enumerate(zip(srch, trh)):
                    src: str = src.strip()
                    tr: str = tr.strip()
                    if bool(src) ^ bool(tr):
                        raise MismatchError(final, i, src, tr)
                    src_m = comment.match(src)
                    tr_m = comment.match(tr)
                    if bool(src_m) ^ bool(tr_m):
                        raise MismatchError(final, i, src, tr)
                    if src_m:
                        if bool(src_m.group(1)) ^ bool(tr_m.group(1)):
                            raise MismatchError(final, i, src, tr)
                        """
                        # skip secions name check - google sometimes translates sections
                        if src_m.group(1) and src_m.group(1).strip() != tr_m.group(1).strip():
                            raise MismatchError(final, i, src, tr)
                        """
                    elif src:
                        db_.add(src, tr)
            do_ts(name, ts)
            db_.close()


if __name__ == "__main__":
    run()
