from argparse import ArgumentParser
from app.http_server import Server, HTTPResponse, HTTPRequest, HTTPStatusCode
import asyncio

parser = ArgumentParser()
parser.add_argument("-d", "--directory", dest="directory", required=False)

server = Server("127.0.0.1", 4221)


@server.get("/")
async def index(request: HTTPRequest):
    return HTTPResponse(HTTPStatusCode.OK)


@server.get("/echo/{content}")
async def echo(request: HTTPRequest, content: str):
    return content


@server.get("/user-agent")
async def headers(request: HTTPRequest):
    return request.headers.get("User-Agent", "")


@server.get("/files/{filename}")
async def get_file(request: HTTPRequest, filename: str):
    file = server.static_dir.joinpath(filename)
    if file.is_file():
        file_data = file.read_text()
        return HTTPResponse(
            HTTPStatusCode.OK, {"Content-Type": "application/octet-stream", "Content-Length": len(file_data)}, file_data
        )
    return HTTPResponse(HTTPStatusCode.NOT_FOUND)


@server.post("/files/{filename}")
async def post_file(request: HTTPRequest, filename: str):
    file_data = request.body
    file = server.static_dir.joinpath(filename)
    file.write_bytes(file_data)
    return HTTPResponse(HTTPStatusCode.CREATED)


if __name__ == "__main__":
    args = parser.parse_args()
    server.set_static_dir(args.directory)
    asyncio.run(server.serve())
