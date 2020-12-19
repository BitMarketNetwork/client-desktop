import enum


class ServerErrorCode(enum.IntEnum):

    broadcastError = 2003


class BaseNetError(Exception):

    def __init__(self, message):
        super().__init__(message)


class JsonError(BaseNetError):

    def __init__(self, msg):
        super().__init__(f"Json format error: {msg}")


class WrongActionError(BaseNetError):

    def __init__(self):
        super().__init__("Wrong action")


class ContentError(BaseNetError):

    def __init__(self, msg):
        super().__init__(f"Content error: {msg}")


class EmptyReplyError(BaseNetError):

    def __init__(self):
        super().__init__("Empty reply")


class ServerError(BaseNetError):

    def __init__(self, message):
        super().__init__(f"Server error: {message}")


class UnknownErrorCode(ServerError):

    def __init__(self, code):
        super().__init__(f"Unknown server error code: {code}")
