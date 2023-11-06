from dataclasses import dataclass
from app.http_server.exceptions import InvalidRequestException
from app.http_server.methods import HTTPMethod
from asyncio import StreamReader


CRLF = "\r\n"


@dataclass
class HTTPRequest:
    method: HTTPMethod
    path: str
    version: str
    headers: dict[str, str]
    body: bytes = None

    @staticmethod
    async def _from_reader(reader: StreamReader) -> "HTTPRequest":
        request_line = await reader.readline()
        try:
            method, request_target, http_version = request_line.decode().replace(CRLF, "").split(" ", 3)
        except (UnicodeDecodeError, ValueError):
            raise InvalidRequestException("Invalid HTTP request line")

        try:
            http_method = HTTPMethod(method.upper())
        except ValueError:
            raise InvalidRequestException("Invalid HTTP Method")

        headers = {}
        while not reader.at_eof():
            data = await reader.readline()
            if data == CRLF.encode():
                break

            try:
                key, value = data.decode().replace(CRLF, "").split(": ", 1)
            except ValueError:
                raise InvalidRequestException("Invalid HTTP header")

            headers[key] = value

        body = None
        match method:
            case HTTPMethod.DELETE | HTTPMethod.PATCH | HTTPMethod.POST | HTTPMethod.PUT:
                try:
                    length = int(headers.get("Content-Length", 0))
                    if length:
                        body = await reader.read(length)
                except ValueError:
                    raise InvalidRequestException("Invalid Content-Length header")

        return HTTPRequest(method=http_method, path=request_target, version=http_version, headers=headers, body=body)
