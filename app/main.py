# check if client supports gzip
accept_encoding = headers.get("accept-encoding", "")
supports_gzip = "gzip" in accept_encoding.lower()

# create base headers
headers_list = [
    "HTTP/1.1 200 OK",
    "Content-Type: text/plain"
]

# set Content-Encoding if gzip is supported
if supports_gzip:
    headers_list.append("Content-Encoding: gzip")

# set content length and body
headers_list.append(f"Content-Length: {len(message)}")
headers_list.append(connection_header.strip())
headers_list.append("")  # blank line to end headers
headers_list.append(message)

# join and send response
response = "\r\n".join(headers_list)
client_socket.sendall(response.encode())
