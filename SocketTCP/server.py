import socket
import threading
import os

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
FILE_LIST_PATH = "files.txt"

# Hàm đọc danh sách file từ file text
def load_file_list():
    files = {}
    with open(FILE_LIST_PATH, "r") as f:
        for line in f:
            name, size = line.strip().split()
            if "MB" in size:
                files[name] = int(size.replace("MB", "")) * 1024 * 1024  # Chuyển MB sang byte
            elif "GB" in size:
                files[name] = int(size.replace("GB", "")) * 1024 * 1024 * 1024  # Chuyển GB sang byte
            elif "B" in size:
                files[name] = int(size.replace("B", ""))  # Nếu không có đơn vị, mặc định là byte
    return files

files = load_file_list()

# Hàm xử lý yêu cầu từ client
def handle_client(client_socket):
    try:
        while True:
            request = client_socket.recv(1024).decode()
            if not request:
                break
            
            command = request.split()
            
            if command[0] == "LIST_FILES":
                response = "\n".join(
                    [
                        f"{name} {size // (1024 * 1024 * 1024)}GB" if size >= 1024 * 1024 * 1024 else \
                        f"{name} {size // (1024 * 1024)}MB" if size >= 1024 * 1024 else \
                        f"{name} {size}B"

                        for name, size in files.items()
                    ]
                )
                client_socket.send(response.encode())
            
            elif command[0] == "DOWNLOAD_REQUEST":
                filename, offset, length = command[1], int(command[2]), int(command[3])
                if filename in files:
                    file_path = os.path.join("source", filename)
                    with open(file_path, "rb") as f:
                        f.seek(offset)
                        data = f.read(length)
                        client_socket.send(data)
                else:
                    client_socket.send("ERROR: File not found".encode())
    finally:
        client_socket.close()

# Khởi tạo server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)

print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()