from app.http_server.response import HTTPStatusCode


class BaseHTTPError(Exception):
    pass


class InvalidRequestError(BaseHTTPError):
    pass


class HTTPError(BaseHTTPError):
    def __init__(self, status_code: HTTPStatusCode, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(message)
