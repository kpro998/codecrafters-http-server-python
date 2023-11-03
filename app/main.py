import socket
from dataclasses import dataclass
from enum import IntEnum


IP = "localhost"
PORT = 4221
BUFFER_SIZE = 1024
CRLF = "\r\n"


class HTTPStatusCode(IntEnum):
    OK = 200
    NOT_FOUND = 404


@dataclass
class HTTPRequest:
    method: str
    path: str
    version: str
    headers: dict[str, str]

    @staticmethod
    def from_raw_http_request(raw: bytes) -> "HTTPRequest":
        http_request_str = raw.decode()
        http_lines = http_request_str.split(CRLF)

        start_line = http_lines.pop(0)
        method, path, version = start_line.split(" ", maxsplit=3)

        headers = {}
        for line in http_lines:
            if line == "":
                continue
            key, value = line.split(": ")
            headers[key] = value

        return HTTPRequest(method, path, version, headers=headers)


@dataclass
class HTTPResponse:
    status_code: HTTPStatusCode
    headers: dict[str, str] = None
    body: str = None
    version: str = "HTTP/1.1"

    def build_response(self) -> str:
        response = ""
        response += f"{self.version} {str(self.status_code)}{CRLF}"

        if self.headers:
            for key, value in self.headers.items():
                response += f"{key}: {value}{CRLF}"
            response += CRLF

        if self.body:
            response += self.body

        response += CRLF
        return response


def main():
    with socket.create_server((IP, PORT)) as server:
        conn, _ = server.accept()
        with conn:
            raw_http_request = conn.recv(BUFFER_SIZE)
            request = HTTPRequest.from_raw_http_request(raw_http_request)
            print(request)

            response: HTTPResponse = None
            match request.path:
                case s if s.startswith("/echo"):
                    body = request.path.replace("/echo/", "", 1)
                    headers = {"Content-Length": str(len(body)), "Content-Type": "text/plain"}
                    response = HTTPResponse(status_code=HTTPStatusCode.OK, headers=headers, body=body)
                case "/user-agent":
                    body = request.headers.get("User-Agent", "")
                    headers = {"Content-Length": str(len(body)), "Content-Type": "text/plain"}
                    response = HTTPResponse(status_code=HTTPStatusCode.OK, headers=headers, body=body)
                case "/":
                    response = HTTPResponse(status_code=HTTPStatusCode.OK)
                case _:
                    response = HTTPResponse(status_code=HTTPStatusCode.NOT_FOUND)

            print(response)
            conn.sendall(response.build_response().encode())


if __name__ == "__main__":
    main()
