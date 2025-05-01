import socket
import threading

def read_request(client_socket):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = client_socket.recv(1024)
        if not chunk:
            break
        data += chunk
    return data.decode()

def parse_headers(request_text):
    lines = request_text.split("\r\n")
    headers = {}
    for line in lines[1:]:
        if line == "":
            break
        if ": " in line:
            key, value = line.split(": ", 1)
            headers[key.lower()] = value
    return headers

def handle_client(client_socket):
    try:
        request_text = read_request(client_socket)
        if not request_text:
            client_socket.close()
            return

        lines = request_text.split("\r\n")
        request_line = lines[0]
        parts = request_line.split()
        if len(parts) != 3:
            client_socket.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.close()
            return

        method, path, version = parts
        headers = parse_headers(request_text)
        accept_encoding = headers.get("accept-encoding", "").lower()
        connection_value = headers.get("connection", "keep-alive").lower()

        # Prepare response
        status_line = "HTTP/1.1 200 OK\r\n"
        body = ""
        response_headers = {
            "Content-Type": "text/plain",
            "Connection": connection_value
        }

        if method == "GET" and path == "/":
            body = "Hello, World!"
        elif method == "GET" and path.startswith("/echo/"):
            body = path[len("/echo/"):]
        else:
            client_socket.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            client_socket.close()
            return

        if "gzip" in accept_encoding:
            response_headers["Content-Encoding"] = "gzip"  # Just declaring, not compressing

        response_headers["Content-Length"] = str(len(body))
        header_lines = [status_line] + [f"{k}: {v}" for k, v in response_headers.items()]
        full_response = "\r\n".join(header_lines) + "\r\n\r\n" + body

        client_socket.sendall(full_response.encode())

        if connection_value == "close":
            client_socket.close()

    except Exception as e:
        print("Error:", e)
        try:
            client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
        except:
            pass
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 4221))
    server_socket.listen(10)
    print("Server listening on port 4221...")

    while True:
        client_sock, _ = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    main()