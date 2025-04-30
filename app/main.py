import socket
import _thread
import sys
import os

# Get the directory from --directory flag
def get_directory():
    args = sys.argv
    if "--directory" in args:
        index = args.index("--directory")
        if index + 1 < len(args):
            return args[index + 1]
    return "."

files_dir = get_directory()

def handle_client(client_socket):
    try:
        data = b""
        while True:
            part = client_socket.recv(1024)
            data += part
            if b"\r\n\r\n" in data:
                break

        headers_end = data.find(b"\r\n\r\n")
        header_part = data[:headers_end].decode()
        body = data[headers_end + 4:]

        lines = header_part.split("\r\n")
        request_line = lines[0]
        headers = {}
        for line in lines[1:]:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        parts = request_line.split()
        if len(parts) < 2:
            response = "HTTP/1.1 400 Bad Request\r\n\r\n"
        else:
            method = parts[0]
            path = parts[1]

            if method == "GET" and path == "/":
                response = "HTTP/1.1 200 OK\r\n\r\n"
                client_socket.sendall(response.encode())

            elif method == "GET" and path.startswith("/echo/"):
                message = path[len("/echo/"):]
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(message)}\r\n"
                    "\r\n"
                    f"{message}"
                )
                client_socket.sendall(response.encode())

            elif method == "GET" and path == "/user-agent":
                user_agent = headers.get("user-agent", "")
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(user_agent)}\r\n"
                    "\r\n"
                    f"{user_agent}"
                )
                client_socket.sendall(response.encode())

            elif method == "GET" and path.startswith("/files/"):
                filename = path[len("/files/"):]
                file_path = os.path.join(files_dir, filename)
                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        content = f.read()
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(content)}\r\n"
                        "\r\n"
                    ).encode() + content
                    client_socket.sendall(response)
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
                    client_socket.sendall(response.encode())

            elif method == "POST" and path.startswith("/files/"):
                filename = path[len("/files/"):]
                file_path = os.path.join(files_dir, filename)
                content_length = int(headers.get("content-length", 0))

                # Read remaining body if not fully read yet
                while len(body) < content_length:
                    body += client_socket.recv(1024)

                # Write to file
                with open(file_path, "wb") as f:
                    f.write(body)

                response = "HTTP/1.1 201 Created\r\n\r\n"
                client_socket.sendall(response.encode())

            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n"
                client_socket.sendall(response.encode())

    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

def main():
    print("Server running on http://localhost:4221 ...")
    server_socket = socket.create_server(("localhost", 4221))
    while True:
        client_socket, _ = server_socket.accept()
        _thread.start_new_thread(handle_client, (client_socket,))

if __name__ == "__main__":
    main()
