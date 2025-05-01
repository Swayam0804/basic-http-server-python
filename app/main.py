import socket
import threading
import os
import sys
import gzip

directory = None

# Parse command-line arguments
if "--directory" in sys.argv:
    idx = sys.argv.index("--directory")
    if idx + 1 < len(sys.argv):
        directory = sys.argv[idx + 1]

def handle_client(client_socket):
    try:
        data = client_socket.recv(4096)
        if not data:
            client_socket.close()
            return

        request = data.decode(errors="ignore").split("\r\n")
        request_line = request[0]
        headers = {}

        i = 1
        while i < len(request) and request[i] != '':
            parts = request[i].split(": ", 1)
            if len(parts) == 2:
                headers[parts[0].lower()] = parts[1]
            i += 1

        method, path, _ = request_line.split()
        body = b""
        if "content-length" in headers:
            content_length = int(headers["content-length"])
            body = data.split(b"\r\n\r\n", 1)[1]
            while len(body) < content_length:
                body += client_socket.recv(4096)

        if method == "GET" and path == "/":
            response = "HTTP/1.1 200 OK\r\n\r\n"
            client_socket.sendall(response.encode())

        elif method == "GET" and path.startswith("/echo/"):
            echo_data = path[6:]
            response_body = echo_data.encode()

            if "accept-encoding" in headers and "gzip" in headers["accept-encoding"]:
                compressed_body = gzip.compress(response_body)
                response_headers = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    "Content-Encoding: gzip",
                    f"Content-Length: {len(compressed_body)}",
                    "\r\n"
                ]
                client_socket.sendall("\r\n".join(response_headers).encode() + compressed_body)
            else:
                response_headers = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f"Content-Length: {len(response_body)}",
                    "\r\n"
                ]
                client_socket.sendall("\r\n".join(response_headers).encode() + response_body)

        elif method == "GET" and path == "/user-agent":
            user_agent = headers.get("user-agent", "")
            body = user_agent.encode()
            response = (
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\n"
                "\r\n"
            )
            client_socket.sendall(response.encode() + body)

        elif method == "GET" and path.startswith("/files/") and directory:
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_data = f.read()
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/octet-stream\r\n"
                    f"Content-Length: {len(file_data)}\r\n"
                    "\r\n"
                )
                client_socket.sendall(response.encode() + file_data)
            else:
                client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

        elif method == "POST" and path.startswith("/files/") and directory:
            filename = path[len("/files/"):]
            filepath = os.path.join(directory, filename)
            with open(filepath, "wb") as f:
                f.write(body)
            client_socket.sendall(b"HTTP/1.1 201 Created\r\n\r\n")

        else:
            client_socket.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

    except Exception as e:
        print(f"Error: {e}")
        client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 4221))
    server_socket.listen(50)
    print("Server running on port 4221...")

    try:
        while True:
            client_socket, _ = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()