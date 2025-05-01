import socket
import threading
import os
import sys

# Get the directory from command-line flag
directory = ""
if "--directory" in sys.argv:
    index = sys.argv.index("--directory")
    if index + 1 < len(sys.argv):
        directory = sys.argv[index + 1]

def handle_client(client_socket):
    data = client_socket.recv(1024).decode()
    if not data:
        client_socket.close()
        return

    lines = data.split("\r\n")
    request_line = lines[0]
    method, path, _ = request_line.split()

    # Parse headers
    headers = {}
    for line in lines[1:]:
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.lower()] = value

    # Determine connection header
    connection_header = "Connection: keep-alive"
    if headers.get("connection", "").lower() == "close":
        connection_header = "Connection: close"

    # Check for gzip support
    accept_encoding = headers.get("accept-encoding", "")
    supports_gzip = "gzip" in accept_encoding.lower()

    response_headers = []
    body = ""

    if method == "GET" and path == "/":
        body = "Hello, World!"
        response_headers.append("HTTP/1.1 200 OK")
        response_headers.append("Content-Type: text/plain")
        if supports_gzip:
            response_headers.append("Content-Encoding: gzip")
        response_headers.append(f"Content-Length: {len(body)}")
        response_headers.append(connection_header)
        response_headers.append("")  # blank line
        response_headers.append(body)
    elif method == "GET" and path.startswith("/echo/"):
        message = path[len("/echo/"):]
        body = message
        response_headers.append("HTTP/1.1 200 OK")
        response_headers.append("Content-Type: text/plain")
        if supports_gzip:
            response_headers.append("Content-Encoding: gzip")
        response_headers.append(f"Content-Length: {len(body)}")
        response_headers.append(connection_header)
        response_headers.append("")
        response_headers.append(body)
    else:
        response_headers = [
            "HTTP/1.1 404 Not Found",
            "Content-Length: 0",
            connection_header,
            "",
            ""
        ]

    response = "\r\n".join(response_headers)
    client_socket.sendall(response.encode())
    if connection_header == "Connection: close":
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 4221))
    server_socket.listen()

    print("Server started on port 4221")

    while True:
        client_sock, addr = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock,))
        thread.start()

if __name__ == "__main__":
    main()