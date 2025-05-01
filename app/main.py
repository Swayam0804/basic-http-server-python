import socket
import threading

def handle_client(client_socket):
    try:
        request = b""
        while b"\r\n\r\n" not in request:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            request += chunk

        if not request:
            client_socket.close()
            return

        request_text = request.decode()
        lines = request_text.split("\r\n")
        request_line = lines[0]
        method, path, _ = request_line.split()

        # Parse headers
        headers = {}
        for line in lines[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key.lower()] = value.strip()
            if line == "":
                break

        accept_encoding = headers.get("accept-encoding", "")
        wants_gzip = "gzip" in accept_encoding

        # Check echo path
        if method == "GET" and path.startswith("/echo/"):
            body = path[len("/echo/"):]
            response = "HTTP/1.1 200 OK\r\n"
            response += "Content-Type: text/plain\r\n"
            if wants_gzip:
                response += "Content-Encoding: gzip\r\n"
            response += f"Content-Length: {len(body)}\r\n"
            response += "\r\n"
            response += body
        else:
            response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"

        client_socket.sendall(response.encode())

    except Exception as e:
        print(f"Error: {e}")
        client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")

    finally:
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 4221))
    server_socket.listen(10)
    print("Listening on port 4221...")

    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    main()
