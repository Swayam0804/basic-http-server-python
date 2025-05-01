import socket
import threading
import os
import sys
import gzip

directory = None

# Check for --directory argument
if "--directory" in sys.argv:
    idx = sys.argv.index("--directory")
    if idx + 1 < len(sys.argv):
        directory = sys.argv[idx + 1]

def handle_client(client_socket):
    buffer = b""
    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break
            buffer += data

            while b"\r\n\r\n" in buffer:
                header_data, buffer = buffer.split(b"\r\n\r\n", 1)
                headers_lines = header_data.decode(errors="ignore").split("\r\n")
                if not headers_lines:
                    break

                request_line = headers_lines[0]
                headers = {}
                for line in headers_lines[1:]:
                    if ": " in line:
                        k, v = line.split(": ", 1)
                        headers[k.lower()] = v

                method, path, _ = request_line.split()

                content_length = int(headers.get("content-length", "0"))
                body = b""
                while len(buffer) < content_length:
                    buffer += client_socket.recv(4096)
                if content_length > 0:
                    body = buffer[:content_length]
                    buffer = buffer[content_length:]

                keep_alive = True
                if headers.get("connection", "").lower() == "close":
                    keep_alive = False

                if method == "GET" and path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\n"
                    client_socket.sendall(response.encode())

                elif method == "GET" and path.startswith("/echo/"):
                    msg = path[len("/echo/"):]
                    response_body = msg.encode()

                    if "accept-encoding" in headers and "gzip" in headers["accept-encoding"]:
                        compressed = gzip.compress(response_body)
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: text/plain\r\n"
                            "Content-Encoding: gzip\r\n"
                            f"Content-Length: {len(compressed)}\r\n"
                        )
                        if not keep_alive:
                            response += "Connection: close\r\n"
                        response += "\r\n"
                        client_socket.sendall(response.encode() + compressed)
                    else:
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: text/plain\r\n"
                            f"Content-Length: {len(response_body)}\r\n"
                        )
                        if not keep_alive:
                            response += "Connection: close\r\n"
                        response += "\r\n"
                        client_socket.sendall(response.encode() + response_body)

                elif method == "GET" and path == "/user-agent":
                    agent = headers.get("user-agent", "")
                    response_body = agent.encode()
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                    )
                    if not keep_alive:
                        response += "Connection: close\r\n"
                    response += "\r\n"
                    client_socket.sendall(response.encode() + response_body)

                elif method == "GET" and path.startswith("/files/") and directory:
                    filename = path[len("/files/"):]
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        with open(filepath, "rb") as f:
                            content = f.read()
                        response = (
                            "HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/octet-stream\r\n"
                            f"Content-Length: {len(content)}\r\n"
                        )
                        if not keep_alive:
                            response += "Connection: close\r\n"
                        response += "\r\n"
                        client_socket.sendall(response.encode() + content)
                    else:
                        response = "HTTP/1.1 404 Not Found\r\n"
                        if not keep_alive:
                            response += "Connection: close\r\n"
                        response += "\r\n"
                        client_socket.sendall(response.encode())

                elif method == "POST" and path.startswith("/files/") and directory:
                    filename = path[len("/files/"):]
                    filepath = os.path.join(directory, filename)
                    with open(filepath, "wb") as f:
                        f.write(body)
                    response = "HTTP/1.1 201 Created\r\n"
                    if not keep_alive:
                        response += "Connection: close\r\n"
                    response += "\r\n"
                    client_socket.sendall(response.encode())

                else:
                    response = "HTTP/1.1 404 Not Found\r\n"
                    if not keep_alive:
                        response += "Connection: close\r\n"
                    response += "\r\n"
                    client_socket.sendall(response.encode())

                if not keep_alive:
                    client_socket.close()
                    return

        except Exception as e:
            print(f"Error: {e}")
            break

    client_socket.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("localhost", 4221))
    s.listen(50)
    print("Listening on port 4221...")

    try:
        while True:
            client_sock, _ = s.accept()
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        s.close()

if __name__ == "__main__":
    main()