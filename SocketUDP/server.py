import socket
import os
import time
import threading
import hashlib

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
FILE_LIST_PATH = "files.txt"
BYTE_SIZE = 4096 - 33  # Adjusted to account for hash size

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
            else:
                # Nếu không có đơn vị, mặc định là byte
                files[name] = int(size)
    return files

# Load file list
files = load_file_list()

# Khởi tạo server UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

print(f"Server is listening on port {SERVER_PORT}...")

current_client = None  # Lưu client hiện tại đang được phục vụ

def handle_download_request(client_address, filename, offset, length):
    if filename in files:
        file_path = os.path.join("source", filename)
        try:
            with open(file_path, "rb") as f:
                f.seek(offset)
                while length > 0:
                    chunk_size = min(BYTE_SIZE, length)
                    data = f.read(chunk_size)
                    hash_value = hashlib.md5(data).hexdigest()
                    packet = hash_value.encode() + b" " + data
                    server_socket.sendto(packet, client_address)
                    length -= chunk_size
                    time.sleep(0.01)  # Add a small delay
                server_socket.sendto(b"End", client_address)
        except ConnectionResetError as e:
            print(f"Error sending file data: {e}")

def handle_list_files_request(client_address):
    response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
    try:
        server_socket.sendto(response.encode(), client_address)
    except ConnectionResetError as e:
        print(f"Error sending LIST_FILES response: {e}")

while True:
    try:
        # Nhận dữ liệu từ client
        data, client_address = server_socket.recvfrom(1024)
        print(f"Received request from {client_address}")
        command = data.decode().split()
        

        if command[0] == "LIST_FILES":
            handle_list_files_request(client_address)

        elif command[0] == "DOWNLOAD_REQUEST":
            filename, offset, length = command[1], int(command[2]), int(command[3])
            download_thread = threading.Thread(target=handle_download_request, args=(client_address, filename, offset, length))
            download_thread.start()

    except Exception as e:
        print(f"Error: {e}")

