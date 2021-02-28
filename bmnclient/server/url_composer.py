
import logging
import PySide2.QtNetwork as qt_network
from urllib.parse import urlencode

log = logging.getLogger(__name__)


class UrlComposer:
    API_HOST = 'https://d1.bitmarket.network:30110'

    def __init__(self, apiver):
        self.__apiver = apiver
        self.__ssl_config = qt_network.QSslConfiguration()

    def get_url(self, action, args=[], gets={}):
        res = f"{self.API_HOST}/v{self.__apiver}/{action}"
        if args:
            res += "/" + "/".join(args)
        if gets:
            res += "?" + urlencode(gets)
        return res

    def get_request(self, action, args, gets=[], verbose=False, ex_host=None, **kwargs):
        if action is None:
            action = ""
        if ex_host:
            uri = ex_host + action
            if gets:
                uri += "?" + urlencode(gets)
        else:
            uri = self.get_url(action, args, gets)
        if verbose:
            log.debug("URL for '%s': %s", args, uri)
        return qt_network.QNetworkRequest(uri)

    def __call__(self, action, **kwargs):
        req = self.get_request(action, **kwargs)
        # warning !!!
        req.setAttribute(qt_network.QNetworkRequest.CacheLoadControlAttribute,
                         qt_network.QNetworkRequest.PreferNetwork)
        req.setPriority(kwargs.get(
            "priority", qt_network.QNetworkRequest.NormalPriority))
        req.setSslConfiguration(self.__ssl_config)
        return req
