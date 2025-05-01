import socket
import threading
import sys
import os

directory = ""

if "--directory" in sys.argv:
    idx = sys.argv.index("--directory")
    if idx + 1 < len(sys.argv):
        directory = sys.argv[idx + 1]

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            request = data.decode(errors="ignore")
            headers = {}
            lines = request.split("\r\n")
            request_line = lines[0]
            parts = request_line.split()

            if len(parts) < 3:
                break

            method, path, _ = parts

            # Parse headers
            i = 1
            while i < len(lines) and lines[i]:
                if ":" in lines[i]:
                    key, value = lines[i].split(":", 1)
                    headers[key.strip().lower()] = value.strip()
                i += 1

            body = request.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in request else ""

            response_headers = []
            response_body = ""

            # Routing
            if method == "GET" and path == "/":
                response_body = ""
                response_headers = ["HTTP/1.1 200 OK", "Content-Length: 0"]
            elif method == "GET" and path.startswith("/echo/"):
                echo_data = path[6:]
                response_body = echo_data
                response_headers = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f"Content-Length: {len(response_body)}"
                ]
                if "accept-encoding" in headers and "gzip" in headers["accept-encoding"]:
                    response_headers.append("Content-Encoding: gzip")
            elif method == "GET" and path == "/user-agent":
                ua = headers.get("user-agent", "")
                response_body = ua
                response_headers = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/plain",
                    f"Content-Length: {len(response_body)}"
                ]
            elif path.startswith("/files/"):
                filename = path[7:]
                file_path = os.path.join(directory, filename)
                if method == "GET":
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            response_body = f.read()
                        response_headers = [
                            "HTTP/1.1 200 OK",
                            "Content-Type: application/octet-stream",
                            f"Content-Length: {len(response_body)}"
                        ]
                    else:
                        response_headers = ["HTTP/1.1 404 Not Found", "Content-Length: 0"]
                        response_body = b""
                elif method == "POST":
                    with open(file_path, "wb") as f:
                        f.write(body.encode())
                    response_headers = ["HTTP/1.1 201 Created", "Content-Length: 0"]
                    response_body = b""
                else:
                    response_headers = ["HTTP/1.1 405 Method Not Allowed", "Content-Length: 0"]
                    response_body = b""
            else:
                response_headers = ["HTTP/1.1 404 Not Found", "Content-Length: 0"]
                response_body = ""

            if "connection" in headers and headers["connection"].lower() == "close":
                response_headers.append("Connection: close")

            if isinstance(response_body, str):
                response_body = response_body.encode()

            response = "\r\n".join(response_headers) + "\r\n\r\n"
            client_socket.sendall(response.encode() + response_body)

            if "connection" in headers and headers["connection"].lower() == "close":
                break

        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("localhost", 4221))
    server_socket.listen(100)
    print("Server listening on port 4221")

    while True:
        client_socket, _ = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    main()
