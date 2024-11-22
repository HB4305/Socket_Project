import socket
import threading
import os

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
# Đường dẫn tới file chứa danh sách file và kích thước
FILE_LIST_PATH = "files.txt"

# Hàm đọc danh sách file từ file text
def load_file_list():
    files = {}
    with open("files.txt", "r") as f:
        for line in f:
            name, size = line.strip().split()
            if "MB" in size:
                files[name] = int(size.replace("MB", "")) * 1024 * 1024  # Chuyển MB sang byte
            elif "GB" in size:
                files[name] = int(size.replace("GB", "")) * 1024 * 1024 * 1024  # Chuyển GB sang byte
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
                response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
                client_socket.send(response.encode())
            
            elif command[0] == "DOWNLOAD_REQUEST":
                filename, offset, length = command[1], int(command[2]), int(command[3])
                if filename in files:
                    with open(filename, "rb") as f:
                        f.seek(offset)
                        data = f.read(length)
                        client_socket.send(f"CHUNK_DATA {filename} {offset} ".encode() + data)
                else:
                    client_socket.send("ERROR: File not found".encode())
    finally:
        client_socket.close()

# Khởi tạo server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)

print("Server is listening on port 12345...")

# Chờ kết nối từ client
while True:
    client_socket, client_address = server_socket.accept()  # Đợi và nhận kết nối từ client
    print(f"Connection established with {client_address}")
    
    # Mỗi client sẽ chạy trên một thread riêng
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()
