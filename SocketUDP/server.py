import socket
import os

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
FILE_LIST_PATH = "C:/Users/ADMIN/Documents/GitHub/Socket_Project/SocketUDP/files.txt"

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
    return files

files = load_file_list()

# Hàm xử lý yêu cầu từ client
def handle_client(data, addr):
    command = data.decode().split()

    if command[0] == "LIST_FILES":
        response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
        server_socket.sendto(response.encode(), addr)
    
    elif command[0] == "DOWNLOAD_REQUEST":
        filename, offset, length = command[1], int(command[2]), int(command[3])
        if filename in files:
            try:
                with open(filename, "rb") as f:
                    f.seek(offset)
                    data = f.read(length)
                    server_socket.sendto(f"CHUNK_DATA {filename} {offset} ".encode() + data, addr)
            except FileNotFoundError:
                server_socket.sendto("ERROR: File not found".encode(), addr)
        else:
            server_socket.sendto("ERROR: File not found".encode(), addr)

# Khởi tạo server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

print("Server is listening on port 12345...")

# Chờ và nhận dữ liệu từ client
while True:
    data, addr = server_socket.recvfrom(1024)  # Nhận dữ liệu từ client
    print(f"Received data from {addr}")
    
    # Xử lý yêu cầu của client (chỉ 1 client tại 1 thời điểm)
    handle_client(data, addr)
