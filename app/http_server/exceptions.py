from app.http_server.response import HTTPStatusCode


class BaseHTTPException(Exception):
    pass


class InvalidRequestException(BaseHTTPException):
    pass


class HTTPError(BaseHTTPException):
    def __init__(self, status_code: HTTPStatusCode, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)
