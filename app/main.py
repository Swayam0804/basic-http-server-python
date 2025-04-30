import socket

def main():
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221))  # No reuse_port on Windows

    while True:
        client_socket, addr = server_socket.accept()
        with client_socket:
            data = client_socket.recv(1024)
            request = data.decode()
            print(request)

            # Get request path
            lines = request.splitlines()
            if len(lines) == 0:
                continue
            request_line = lines[0]  # e.g., GET /echo/hello HTTP/1.1
            parts = request_line.split()
            if len(parts) < 2:
                continue

            method, path = parts[0], parts[1]

            if method == "GET":
                if path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\n"
                elif path.startswith("/echo/"):
                    echo_str = path[len("/echo/"):]  # extract string
                    response_body = echo_str
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "\r\n"
                        f"{response_body}"
                    )
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"
            else:
                response = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"

            client_socket.sendall(response.encode())

if __name__ == "__main__":
    main()