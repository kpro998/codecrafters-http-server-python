import asyncio
from dataclasses import dataclass
from enum import IntEnum
from argparse import ArgumentParser
from pathlib import Path


IP = "localhost"
PORT = 4221
BUFFER_SIZE = 1024
CRLF = "\r\n"


parser = ArgumentParser()
parser.add_argument("-d", "--directory", dest="directory")


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


def get_file_from_directory(directory: Path, filename: str) -> str | None:
    file = directory.joinpath(filename)
    if file.is_file():
        return file.read_text()
    return None


def get_response_from_request(request: HTTPRequest) -> HTTPResponse:
    response: HTTPResponse = None
    match request.path:
        case s if s.startswith("/echo"):
            body = request.path.replace("/echo/", "", 1)
            headers = {"Content-Length": str(len(body)), "Content-Type": "text/plain"}
            response = HTTPResponse(status_code=HTTPStatusCode.OK, headers=headers, body=body)
        case s if s.startswith("/files"):
            filename = request.path.replace("/files/", "", 1)
            file = get_file_from_directory(Path(args.directory), filename)
            if file != None:
                headers = {"Content-Length": str(len(file)), "Content-Type": "application/octet-stream"}
                response = HTTPResponse(status_code=HTTPStatusCode.OK, headers=headers, body=file)
            else:
                response = HTTPResponse(status_code=HTTPStatusCode.NOT_FOUND)
        case "/user-agent":
            body = request.headers.get("User-Agent", "")
            headers = {"Content-Length": str(len(body)), "Content-Type": "text/plain"}
            response = HTTPResponse(status_code=HTTPStatusCode.OK, headers=headers, body=body)
        case "/":
            response = HTTPResponse(status_code=HTTPStatusCode.OK)
        case _:
            response = HTTPResponse(status_code=HTTPStatusCode.NOT_FOUND)
    return response


async def client_connected(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    print(f"Got connection from {addr}")

    data = await reader.read(BUFFER_SIZE)
    request = HTTPRequest.from_raw_http_request(data)
    print(request)

    response = get_response_from_request(request)
    print(response)

    writer.write(response.build_response().encode())
    await writer.drain()

    writer.close()
    await writer.wait_closed()
    print(f"Connection with {addr} closed")


async def main():
    server = await asyncio.start_server(client_connected, IP, PORT)
    print(f"Server listening on {IP}:{PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    args = parser.parse_args()
    asyncio.run(main())
