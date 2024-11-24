import socket
import os
import time
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
FILE_LIST_PATH = "files.txt"
MAX_CHUNK_SIZE = 1024  # Kích thước tối đa của một chunk dữ liệu

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

files = load_file_list()

# Hàm xử lý yêu cầu từ client
def handle_client(client_socket, client_address):
    try:
        while True:
            request = client_socket.recvfrom(1024)
            message, client_address = request

            if not message:
                break
            
            command = message.decode().split()
            
            if command[0] == "LIST_FILES":
                response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
                client_socket.sendto(response.encode(), client_address)
            
            elif command[0] == "DOWNLOAD_REQUEST":
                filename, offset, length = command[1], int(command[2]), int(command[3])
                if filename in files:
                    file_path = os.path.join("source", filename)
                    with open(file_path, "rb") as f:
                        f.seek(offset)
                        chunk_data = f.read(length)
                        sequence_number = 0  # Số thứ tự của chunk
                        while chunk_data:
                            # Gửi chunk dữ liệu
                            client_socket.sendto(f"{sequence_number}".encode(), client_address)
                            client_socket.sendto(chunk_data, client_address)
                            
                            # Chờ ACK từ client
                            client_socket.settimeout(1)  # Thời gian chờ ACK
                            try:
                                ack, _ = client_socket.recvfrom(1024)
                                ack = ack.decode()
                                if ack == f"ACK_{sequence_number}":
                                    print(f"Received ACK for sequence number {sequence_number}")
                                    sequence_number += 1
                                else:
                                    print(f"Received NACK for sequence number {sequence_number}, resending...")
                                    client_socket.sendto(f"{sequence_number}".encode(), client_address)
                                    client_socket.sendto(chunk_data, client_address)
                            except socket.timeout:
                                print(f"Timeout waiting for ACK for sequence number {sequence_number}, resending...")
                                client_socket.sendto(f"{sequence_number}".encode(), client_address)
                                client_socket.sendto(chunk_data, client_address)
                                
                            chunk_data = f.read(length)  # Đọc tiếp chunk dữ liệu tiếp theo
                else:
                    client_socket.sendto("ERROR: File not found".encode(), client_address)
    finally:
        client_socket.close()

# Khởi tạo server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

print("Server is listening on port 12345...")

# Chờ kết nối từ client
while True:
    message, client_address = server_socket.recvfrom(1024)
    print(f"Connection established with {client_address}")
    
    # Mỗi client sẽ chạy trên một thread riêng
    client_thread = threading.Thread(target=handle_client, args=(server_socket, client_address))
    client_thread.start()
