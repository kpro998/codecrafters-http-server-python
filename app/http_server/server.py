from asyncio import start_server, StreamReader, StreamWriter, Server
from typing import Callable
from app.http_server.methods import HTTPMethod
from app.http_server.response import HTTPResponse, HTTPStatusCode
from app.http_server.request import HTTPRequest
from app.http_server.exceptions import InvalidRequestException, HTTPError
from app.http_server.route import Route
from pathlib import Path
import logging

HTTPCallback = Callable[[HTTPRequest], HTTPResponse]


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

    def add_route(self, method: HTTPMethod, path: str, callback: Callable) -> None:
        self.routes.append(Route(method, path, callback))

    def get_route(self, method: HTTPMethod, path: str) -> Route | None:
        for route in self.routes:
            if route.method == method and route.path_matches_regex(path):
                return route

    async def serve(self, static_dir: Path | str = None) -> None:
        self.server = await start_server(self._client_connected_callback, self.host, self.port)
        logging.info(f"Server listening on {self.host}:{self.port}")
        await self.server.serve_forever()

    async def _client_connected_callback(self, reader: StreamReader, writer: StreamWriter) -> None:
        addr = writer.get_extra_info("peername")
        logging.debug(f"Got connection from {addr}")

        try:
            request = await HTTPRequest._from_reader(reader)
        except InvalidRequestException:
            logging.debug(f"Connection {addr} sent invalid request")
            return await self._close_writer(writer)

        try:
            route = self.get_route(request.method, request.path)
            if route:
                logging.debug(f"Path '{request.path}' matches route regex: {route.path_regex}")
                variables = route.parse_path(request.path)
                ret = await route.callback(request, **variables)
                match ret:
                    case HTTPResponse():
                        await self._respond(writer, ret)
                    case str():
                        response = HTTPResponse(
                            HTTPStatusCode.OK, {"Content-Length": len(ret), "Content-Type": "text/plain"}, ret
                        )
                        await self._respond(writer, response)
                    case _:
                        raise HTTPError(HTTPStatusCode.INTERNAL_SERVER_ERROR, "Internal server error")
            logging.warn(f"404 Not found: {request.path}")
            raise HTTPError(HTTPStatusCode.NOT_FOUND, f"404 Could not find path '{request.path}'")
        except Exception as e:
            match e:
                case HTTPError():
                    return await self._respond(writer, HTTPResponse(e.status_code))
                case _:
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
        def wrapper(func: Callable) -> None:
            self.add_route(HTTPMethod.GET, route, func)

        return wrapper

    def post(self, route: str) -> Callable:
        def wrapper(func: Callable) -> None:
            self.add_route(HTTPMethod.POST, route, func)

        return wrapper
