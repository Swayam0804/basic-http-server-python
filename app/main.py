import socket  # noqa: F401
  
def main():
    print("Logs from your program will appear here!")
  
    # Start the server on localhost:4221
    server_socket = socket.create_server(("localhost", 4221))  # Removed reuse_port
  
    client_socket, addr = server_socket.accept()  # wait for client
    with client_socket:
        data = client_socket.recv(1024)
        request = data.decode()
        print(request)
  
        # Parse the HTTP request
        if request.startswith("GET / HTTP/1.1"):
            response = "HTTP/1.1 200 OK\r\n\r\n"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"
        client_socket.sendall(response.encode())
  
if __name__ == "__main__":
    main()