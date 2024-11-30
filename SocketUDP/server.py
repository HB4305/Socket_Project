# import socket
# import os

# SERVER_HOST = "127.0.0.1"
# SERVER_PORT = 12345
# FILE_LIST_PATH = "files.txt"


# # Hàm đọc danh sách file từ file text
# def load_file_list():
#     files = {}
#     with open(FILE_LIST_PATH, "r") as f:
#         for line in f:
#             name, size = line.strip().split()
#             if "MB" in size:
#                 files[name] = int(size.replace("MB", "")) * 1024 * 1024  # Chuyển MB sang byte
#             elif "GB" in size:
#                 files[name] = int(size.replace("GB", "")) * 1024 * 1024 * 1024  # Chuyển GB sang byte
#             else:
#                 # Nếu không có đơn vị, mặc định là byte
#                 files[name] = int(size)
#     return files


# files = load_file_list()


# # Hàm xử lý yêu cầu từ client
# def handle_client(data, client_address, server_socket):
#     request = data.decode()
#     command = request.split()

#     if command[0] == "LIST_FILES":
#         response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
#         server_socket.sendto(response.encode(), client_address)

#     elif command[0] == "DOWNLOAD_REQUEST":
#         filename, offset, length = command[1], int(command[2]), int(command[3])
#         if filename in files:
#             file_path = os.path.join("source", filename)
#             with open(file_path, "rb") as f:
#                 f.seek(offset)
#                 while length > 0:
#                     chunk_size = min(1024, length)
#                     data = f.read(chunk_size)
#                     server_socket.sendto(data, client_address)
#                     length -= chunk_size
#                     server_socket.sendto(b"End", client_address)
#         else:
#             server_socket.sendto("ERROR: File not found".encode(), client_address)


# # Khởi tạo server UDP
# server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# server_socket.bind((SERVER_HOST, SERVER_PORT))

# print("Server is listening on port 12345...")

# # Chờ yêu cầu từ client
# while True:
#     data, client_address = server_socket.recvfrom(1024)  # Nhận dữ liệu từ client
#     print(f"Connection established with {client_address}")
#     handle_client(data, client_address, server_socket)
import socket
import os
import time

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

while True:
    try:
        data, client_address = server_socket.recvfrom(1024)  # Nhận dữ liệu từ client
        print(f"Connection established with {client_address}")
        command = data.decode().split()

        if command[0] == "LIST_FILES":
            response = "\n".join([f"{name} {size // (1024 * 1024)}MB" for name, size in files.items()])
            try:
                server_socket.sendto(response.encode(), client_address)
            except ConnectionResetError as e:
                print(f"Error sending LIST_FILES response: {e}")

        elif command[0] == "DOWNLOAD_REQUEST":
            filename, offset, length = command[1], int(command[2]), int(command[3])
            if filename in files:
                file_path = os.path.join("source", filename)
                try:
                    with open(file_path, "rb") as f:
                        f.seek(offset)
                        while length > 0:
                            chunk_size = min(1024, length)
                            data = f.read(chunk_size)
                            server_socket.sendto(data, client_address)
                            length -= chunk_size
                            time.sleep(0.01)  # Add a small delay
                        server_socket.sendto(b"End", client_address)
                except ConnectionResetError as e:
                    print(f"Error sending file data: {e}")
            else:
                try:
                    server_socket.sendto("ERROR: File not found".encode(), client_address)
                except ConnectionResetError as e:
                    print(f"Error sending file not found message: {e}")

    except ConnectionResetError as e:
        print(f"Error receiving data: {e}")