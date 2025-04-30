import socket
import _thread
import sys
import os

# Get the directory passed via --directory flag
def get_directory():
    args = sys.argv
    if "--directory" in args:
        index = args.index("--directory")
        if index + 1 < len(args):
            return args[index + 1]
    return "."  # default to current dir

files_dir = get_directory()

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

            elif method == "GET" and path.startswith("/files/"):
                filename = path[len("/files/"):]
                file_path = os.path.join(files_dir, filename)

                if os.path.isfile(file_path):
                    with open(file_path, "rb") as f:
                        content = f.read()
                    response_headers = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: application/octet-stream\r\n"
                        f"Content-Length: {len(content)}\r\n"
                        "\r\n"
                    )
                    client_socket.sendall(response_headers.encode() + content)
                    client_socket.close()
                    return
                else:
                    response = "HTTP/1.1 404 Not Found\r\n\r\n"

            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

        client_socket.sendall(response.encode())

    except Exception as e:
        print("Error:", e)
    finally:
        client_socket.close()

def main():
    print("Server running on http://localhost:4221 ...")
    server_socket = socket.create_server(("localhost", 4221))
    while True:
        client_socket, addr = server_socket.accept()
        _thread.start_new_thread(handle_client, (client_socket,))

if __name__ == "__main__":
    main()