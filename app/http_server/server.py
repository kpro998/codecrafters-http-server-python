from asyncio import start_server, StreamReader, StreamWriter, Server
from typing import Callable
from app.http_server.methods import HTTPMethod
from app.http_server.response import HTTPResponse, HTTPStatusCode
from app.http_server.request import HTTPRequest
from app.http_server.exceptions import InvalidRequestException, HTTPError
from app.http_server.route import Route
from app.http_server.types import HTTPCallback
from pathlib import Path
import logging


class Server:
    def __init__(self, host: str, port: str) -> None:
        self.host = host
        self.port = port
        self.server: Server = None
        self.routes: list[Route] = []
        self.static_dir: Path = None

    def set_static_dir(self, static_dir: Path | str | None):
        if static_dir:
            self.static_dir = Path(static_dir)

    def add_route(self, method: HTTPMethod, path: str, callback: HTTPCallback) -> None:
        self.routes.append(Route(method, path, callback))

    def get_route(self, method: HTTPMethod, path: str) -> Route | None:
        for route in self.routes:
            if route.method == method and route.path_matches_regex(path):
                return route

    async def serve(self) -> None:
        self.server = await start_server(self._client_connected_callback, self.host, self.port)
        logging.info(f"Server listening on {self.host}:{self.port}")
        await self.server.serve_forever()

    async def _client_connected_callback(self, reader: StreamReader, writer: StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logging.debug(f"Got connection from {addr}")

        try:
            request = await HTTPRequest._from_reader(reader)
        except InvalidRequestException as e:
            raise HTTPError(HTTPStatusCode.BAD_REQUEST, str(e))

        try:
            route = self.get_route(request.method, request.path)
            if not route:
                raise HTTPError(HTTPStatusCode.NOT_FOUND, f"Could not find path '{request.path}'")

            logging.debug(f"Path '{request.path}' matches route regex: {route.path_regex}")

            response = HTTPResponse(HTTPStatusCode.INTERNAL_SERVER_ERROR)

            variables = route.parse_path(request.path)
            ret = await route.callback(request, **variables)
            match ret:
                case HTTPResponse():
                    response = ret
                case str():
                    response = HTTPResponse(
                        HTTPStatusCode.OK, {"Content-Length": len(ret), "Content-Type": "text/plain"}, ret
                    )
                case _:
                    raise NotImplementedError(f"We do not support type '{type(ret)}' yet")

            logging.info(f"{addr[0]}:{addr[1]} {request.path} {response.status_code}")
            await self._respond(writer, response)
        except HTTPError:
            logging.warn(str(e))
            return await self._respond(writer, HTTPResponse(e.status_code))
        except Exception as e:
            logging.exception(e)
            return await self._respond(writer, HTTPResponse(HTTPStatusCode.INTERNAL_SERVER_ERROR))

    async def _close_writer(self, writer: StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        writer.close()
        await writer.wait_closed()
        logging.debug(f"Connection with {addr} closed")

    async def _respond(self, writer: StreamWriter, response: HTTPResponse, close_writer: bool = True) -> None:
        writer.write(response.build_response().encode())
        await writer.drain()

        if close_writer:
            await self._close_writer(writer)

    def get(self, route: str) -> Callable:
        def wrapper(func: HTTPCallback) -> None:
            self.add_route(HTTPMethod.GET, route, func)

        return wrapper

    def post(self, route: str) -> Callable:
        def wrapper(func: HTTPCallback) -> None:
            self.add_route(HTTPMethod.POST, route, func)

        return wrapper
