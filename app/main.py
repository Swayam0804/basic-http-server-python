import socket

def main():
    print("Server is starting on http://localhost:4221 ...")

    # Create a TCP server socket
    server_socket = socket.create_server(("localhost", 4221))

    while True:
        # Wait for a client connection
        client_socket, address = server_socket.accept()
        print("Connected to", address)

        # Read request from client
        data = client_socket.recv(1024)
        if not data:
            client_socket.close()
            continue

        # Decode bytes to string
        request = data.decode()
        lines = request.split("\r\n")

        # First line: e.g., "GET /user-agent HTTP/1.1"
        request_line = lines[0]
        parts = request_line.split()

        if len(parts) < 2:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"
        else:
            method = parts[0]
            path = parts[1]

            # Check for valid GET request
            if method == "GET":
                if path == "/":
                    response = "HTTP/1.1 200 OK\r\n\r\nHello, World!"

                elif path.startswith("/echo/"):
                    message = path[len("/echo/"):]  # Get the part after /echo/
                    response_body = message
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "\r\n"
                        f"{response_body}"
                    )

                elif path == "/user-agent":
                    # Loop through headers to find User-Agent
                    user_agent = ""
                    for line in lines:
                        if line.lower().startswith("user-agent:"):
                            user_agent = line.split(":", 1)[1].strip()
                            break

                    response_body = user_agent
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/plain\r\n"
                        f"Content-Length: {len(response_body)}\r\n"
                        "\r\n"
                        f"{response_body}"
                    )

                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

            else:
                response = "HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed"

        # Send the response to the client
        client_socket.sendall(response.encode())

        # Close the connection
        client_socket.close()

if __name__ == "__main__":
    main()
