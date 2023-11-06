from dataclasses import dataclass
from enum import IntEnum

CRLF = "\r\n"


class HTTPStatusCode(IntEnum):
    OK = 200
    CREATED = 201
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


@dataclass
class HTTPResponse:
    status_code: HTTPStatusCode
    headers: dict[str, str] = None
    body: str = None
    version: str = "HTTP/1.1"

    def build_response(self) -> str:
        response = f"{self.version} {str(self.status_code)}{CRLF}"

        if self.headers:
            for key, value in self.headers.items():
                response += f"{key}: {value}{CRLF}"
            response += CRLF

        if self.body:
            response += self.body

        response += CRLF
        return response
