class BaseHTTPException(Exception):
    pass


class InvalidRequestException(BaseHTTPException):
    pass


class HTTPError(BaseHTTPException):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)
