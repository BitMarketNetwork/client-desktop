
import logging
import PySide2.QtNetwork as qt_network
from urllib.parse import urlencode

log = logging.getLogger(__name__)


class UrlComposer:
    API_HOST = 'https://d1.bitmarket.network:30110'

    def __init__(self, apiver):
        self._apiver = apiver

    def get_url(self, action, args=[], gets={}):
        res = f"{self.API_HOST}/v{self._apiver}/{action}"
        if args:
            res += "/" + "/".join(args)
        if gets:
            res += "?" + urlencode(gets)
        return res

    def get_request(self, action, args, gets=[], verbose=False, ex_host=None):
        if ex_host:
            uri = ex_host + action
            if gets:
                uri += "/?" + urlencode(gets)
        else:
            uri = self.get_url(action, args, gets)
        if verbose:
            log.debug("URL for '%s': %s", args, uri)
        return qt_network.QNetworkRequest(uri)

    def __call__(self, action, **kwargs):
        return self.get_request(action, **kwargs)
