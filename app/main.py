# Uncomment this to pass the first stage
import socket
from dataclasses import dataclass


@dataclass
class HTTPRequest:
    method: str
    path: str
    version: str


def parse_raw_http_request(raw: bytes):
    http_request_str = raw.decode()
    http_lines = http_request_str.split("\r\n")

    start_line = http_lines[0]
    method, path, version = start_line.split(" ", maxsplit=3)
    return HTTPRequest(method, path, version)


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221))
    conn, addr = server_socket.accept()  # wait for client
    raw_http_request = conn.recv(1024)
    request = parse_raw_http_request(raw_http_request)

    if request.path == "/":
        conn.sendall("HTTP/1.1 200 OK\r\n\r\n".encode())
    else:
        conn.sendall("HTTP/1.1 404 Not Found\r\n\r\n".encode())

    conn.close()
    server_socket.close


if __name__ == "__main__":
    main()
