import socket
import os
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

def format_size(size):
    if size >= 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"
    elif size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    elif size >= 1024:
        return f"{size / 1024:.1f}KB"
    else:
        return f"{size}B"

# Load file list
files = load_file_list()

# Khởi tạo server UDP
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

print(f"Server is listening on port {SERVER_PORT}...")

def handle_download_request(client_address, filename):
    if filename in files:
        file_path = os.path.join("source", filename)
        if not os.path.exists(file_path):
            server_socket.sendto(b"Error: File not found", client_address)
            return

        try:
            length = os.path.getsize(file_path)
            with open(file_path, "rb") as f:
                seq = 0  # Sequence number bắt đầu từ 0
                while length > 0:
                    data = f.read(min(BYTE_SIZE, length))
                    hash_value = hashlib.md5(data).hexdigest()
                    packet = f"{seq:08d}".encode() + b" " + hash_value.encode() + b" " + data
                    server_socket.sendto(packet, client_address)
                    # Wait for ACK or NACK
                    while True:
                        server_socket.settimeout(0.01)  # Timeout để chờ ACK hoặc NACK
                        try:
                            ack, _ = server_socket.recvfrom(1024)
                            ack_message = ack.decode()
                            if ack_message == f"ACK {seq}":
                                seq += 1  # Chỉ tăng seq nếu nhận được ACK đúng
                                length -= len(data)
                                break
                            elif ack_message == f"NACK {seq}":
                                server_socket.sendto(packet, client_address)  # Resend nếu nhận được NACK
                        except socket.timeout:
                            print(f"Lost packet {seq}, resending...")
                            server_socket.sendto(packet, client_address)  # Resend nếu không có ACK/NACK
                
            server_socket.sendto(b"End", client_address)
        except ConnectionResetError as e:
            print(f"Error sending file data: {e}")
    else:
        server_socket.sendto(b"Error: File not found", client_address)

def handle_list_files_request(client_address):
    response = "\n".join([f"{name} {format_size(size)}" for name, size in files.items()])
    try:
        server_socket.sendto(response.encode(), client_address)
    except ConnectionResetError as e:
        print(f"Error sending LIST_FILES response: {e}")
def main_server():
    while True:
        try:
            # Nhận dữ liệu từ client
            data, client_address = server_socket.recvfrom(1024)
            print(f"Received request from {client_address}")
            command = data.decode().split()
            
            if command[0] == "LIST_FILES":
                handle_list_files_request(client_address)

            elif command[0] == "DOWNLOAD_REQUEST":
                filename = command[1]
                handle_download_request(client_address, filename)

        except Exception as e:
            continue

if __name__ == "__main__":
    main_server()