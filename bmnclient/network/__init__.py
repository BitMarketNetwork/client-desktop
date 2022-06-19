import logging

from PySide6.QtNetwork import QSslSocket

from ..logger import Logger
from ..os_environment import Platform
from ..utils import NotImplementedInstance


class Network(NotImplementedInstance):
    __initialized = False

    @classmethod
    def configure(cls) -> None:
        logger = Logger.classLogger(cls)

        # Protection: qt.network.ssl: Cannot set backend named "..." as active,
        # another backend is already in use
        if not cls.__initialized:
            logger.debug(
                "QSslSocket available backends: [%s]",
                ", ".join(QSslSocket.availableBackends())
            )

            if Platform.isWindows:
                backend = "schannel"
            elif Platform.isDarwin:
                backend = "securetransport"
            else:
                backend = "openssl"

            if (
                    not QSslSocket.setActiveBackend(backend)
                    or not QSslSocket.supportsSsl()
            ):
                Logger.fatal(
                    "Platform doesn't support TLS, failed to set backend '{}'."
                    .format(backend),
                    logger)
            cls.__initialized = True

        if logger.isEnabledFor(logging.DEBUG):
            version_string = QSslSocket.sslLibraryVersionString()
            version_number = QSslSocket.sslLibraryVersionNumber()
            if version_number > 0:
                version_number = " (0x{:08x})".format(version_number)
            else:
                version_number = ""
            logger.debug(
                "QSslSocket TLS status:"
                "\n\tBackend: %s"
                "\n\tVersion: %s%s",
                QSslSocket.activeBackend(),
                version_string,
                version_number)
