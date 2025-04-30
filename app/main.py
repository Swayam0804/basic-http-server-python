import socket
import _thread  # low-level, procedural threading

def handle_client(client_socket):
    try:
        data = client_socket.recv(1024)
        if not data:
            client_socket.close()
            return

        request = data.decode()
        lines = request.split("\r\n")
        request_line = lines[0]

        parts = request_line.split()
        if len(parts) < 2:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"
        else:
            method = parts[0]
            path = parts[1]

            if method == "GET" and path == "/":
                response = "HTTP/1.1 200 OK\r\n\r\n"
            elif method == "GET" and path.startswith("/echo/"):
                message = path[len("/echo/"):]
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(message)}\r\n"
                    "\r\n"
                    f"{message}"
                )
            elif method == "GET" and path == "/user-agent":
                user_agent = ""
                for line in lines:
                    if line.lower().startswith("user-agent:"):
                        user_agent = line.split(":", 1)[1].strip()
                        break
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    f"Content-Length: {len(user_agent)}\r\n"
                    "\r\n"
                    f"{user_agent}"
                )
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

        client_socket.sendall(response.encode())
    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

def main():
    print("Starting server on http://localhost:4221 ...")
    server_socket = socket.create_server(("localhost", 4221))

    while True:
        client_socket, addr = server_socket.accept()
        print("Connected to:", addr)
        _thread.start_new_thread(handle_client, (client_socket,))

if __name__ == "__main__":
    main()
