import asyncio
from argparse import ArgumentParser

from app.http_server import HTTPRequest, HTTPResponse, HTTPServer, HTTPStatusCode

parser = ArgumentParser()
parser.add_argument("-d", "--directory", dest="directory", required=False)

server = HTTPServer("127.0.0.1", 4221)


@server.get("/")
async def index(_: HTTPRequest) -> HTTPResponse:
    return HTTPResponse(HTTPStatusCode.OK)


@server.get("/echo/{content}")
async def echo(_: HTTPRequest, content: str) -> str:
    return content


@server.get("/user-agent")
async def headers(request: HTTPRequest) -> str:
    return request.headers.get("User-Agent", "")


@server.get("/files/{filename}")
async def get_file(_: HTTPRequest, filename: str) -> HTTPResponse:
    if not server.static_dir:
        return HTTPResponse(HTTPStatusCode.INTERNAL_SERVER_ERROR)

    file = server.static_dir.joinpath(filename)
    if file.is_file():
        file_data = file.read_text()#
        headers = {"Content-Type": "application/octet-stream","Content-Length": len(file_data)}
        return HTTPResponse(HTTPStatusCode.OK, headers, file_data)
    return HTTPResponse(HTTPStatusCode.NOT_FOUND)


@server.post("/files/{filename}")
async def post_file(request: HTTPRequest, filename: str) -> HTTPResponse:
    if not server.static_dir:
        return HTTPResponse(HTTPStatusCode.INTERNAL_SERVER_ERROR)

    if not request.body:
        return HTTPResponse(HTTPStatusCode.BAD_REQUEST)

    file = server.static_dir.joinpath(filename)
    file.write_bytes(request.body)
    return HTTPResponse(HTTPStatusCode.CREATED)


if __name__ == "__main__":
    args = parser.parse_args()
    server.set_static_dir(args.directory)
    asyncio.run(server.serve())
