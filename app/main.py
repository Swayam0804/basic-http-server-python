import socket
import _thread
import sys
import os

def get_directory():
    args = sys.argv
    if "--directory" in args:
        idx = args.index("--directory")
        if idx + 1 < len(args):
            return args[idx + 1]
    return "."

files_dir = get_directory()

def handle_client(client_socket):
    try:
        while True:
            data = b""
            while True:
                part = client_socket.recv(1024)
                if not part:
                    return
                data += part
                if b"\r\n\r\n" in data:
                    break

            headers_end = data.find(b"\r\n\r\n")
            header_part = data[:headers_end].decode()
            body = data[headers_end + 4:]

            lines = header_part.split("\r\n")
            if len(lines) == 0:
                break

            request_line = lines[0]
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()

            parts = request_line.split()
            if len(parts) < 2:
                client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
                break

            method = parts[0]
            path = parts[1]

            connection_close = headers.get("connection", "").lower() == "close"
            connection_header = "Connection: close\r\n" if connection_close else "Connection: keep-alive\r\n"

            if method == "GET" and path == "/":
                response = "HTTP/1.1 200 OK\r\n" + connection_header + "\r\n"
                client_socket.sendall(response.encode())

            elif method == "GET" and path.startswith("/echo/"):
                message = path[len("/echo/"):]
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    f"{connection_header}"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(message)}\r\n\r\n"
                    f"{message}"
                )
                client_socket.sendall(response.encode())

            elif method == "GET" and path == "/user-agent":
                ua = headers.get("user-agent", "")
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    f"{connection_header}"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(ua)}\r\n\r\n"
                    f"{ua}"
                )
                client_socket.sendall(response.encode())

            elif method == "GET" and path.startswith("/files/"):
                filename = path[len("/files/"):]
                filepath = os.path.join(files_dir, filename)
                if os.path.isfile(filepath):
                    with open(filepath, "rb") as f:
                        content = f.read()
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        f"{connection_header}"
                        "Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(content)}\r\n\r\n"
                    ).encode() + content
                    client_socket.sendall(response)
                else:
                    response = f"HTTP/1.1 404 Not Found\r\n{connection_header}\r\n"
                    client_socket.sendall(response.encode())

            elif method == "POST" and path.startswith("/files/"):
                filename = path[len("/files/"):]
                filepath = os.path.join(files_dir, filename)
                content_length = int(headers.get("content-length", 0))

                while len(body) < content_length:
                    body += client_socket.recv(1024)

                with open(filepath, "wb") as f:
                    f.write(body)

                response = f"HTTP/1.1 201 Created\r\n{connection_header}\r\n"
                client_socket.sendall(response.encode())

            else:
                response = f"HTTP/1.1 404 Not Found\r\n{connection_header}\r\n"
                client_socket.sendall(response.encode())

            if connection_close:
                break

    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

def main():
    print("Server running at http://localhost:4221")
    server_socket = socket.create_server(("localhost", 4221))
    server_socket.listen()

    while True:
        client_socket, _ = server_socket.accept()
        _thread.start_new_thread(handle_client, (client_socket,))

if __name__ == "__main__":
    main()
