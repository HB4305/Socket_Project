import socket
import os
import time
import hashlib
import sys

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 4096 - 33  # Adjusted to account for hash size

def print_progress_bar(iteration, total, length=50):
    percent = 100 * (iteration / float(total)) 
    percent = min(percent, 100) 
    filled_length = int(length * iteration // total)
    bar = '#' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r|{bar}| {percent:.1f}% Complete')
    sys.stdout.flush()

def download_file(file_name, file_size):
    """Tải file với giới hạn kích thước yêu cầu."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(f"DOWNLOAD_REQUEST {file_name} {file_size}".encode(), (SERVER_HOST, SERVER_PORT))
    length, _ = sock.recvfrom(4096)  # Nhận kích thước file từ server
    length = int(length.decode())
    src_hash, _ = sock.recvfrom(4096)  # Nhận hash của file từ server
    src_hash = src_hash.decode()
    with open(file_name, "wb") as f:
        total_received = 0  # Tổng số byte đã nhận
        expected_seq = 0  # Sequence number bắt đầu từ 0
        while True:
            data, _ = sock.recvfrom(CHUNK_SIZE + 42)
            if data == b"End":
                break

            seq = int(data[:8].decode().strip())
            hash_value, chunk_data = data[9:41], data[42:]
            if seq == expected_seq and hashlib.md5(chunk_data).hexdigest() == hash_value.decode():
                f.write(chunk_data)
                total_received += len(chunk_data)
                print_progress_bar(total_received, length)
                sock.sendto(f"ACK {seq}".encode(), (SERVER_HOST, SERVER_PORT))  # Gửi ACK cho server
                expected_seq += 1
            else:
                sock.sendto(f"NACK {expected_seq}".encode(), (SERVER_HOST, SERVER_PORT))  # Gửi NACK cho server
    sock.close()
    print()

    # Verify the file hash
    with open(file_name, "rb") as f:
        des_hash = hashlib.md5(f.read()).hexdigest()
    if des_hash == src_hash:
        print(f"File {file_name} downloaded successfully and verified.")
    else:
        print(f"File {file_name} downloaded failed. Retrying...")
        download_file(file_name, file_size)

def request_file_list():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto("LIST_FILES".encode(), (SERVER_HOST, SERVER_PORT))
    file_list, _ = sock.recvfrom(4096)  # Nhận danh sách file từ server
    file_list = file_list.decode().splitlines()
    sock.close()
    return file_list

def display_file_list(file_list):
    print("Available files on server:")
    for file in file_list:
        print("-", file)

def parse_size(size_str):
    if size_str.endswith("MB"):
        return int(float(size_str.replace("MB", "")) * 1024 * 1024)
    elif size_str.endswith("GB"):
        return int(float(size_str.replace("GB", "")) * 1024 * 1024 * 1024)
    elif size_str.endswith("KB"):
        return int(float(size_str.replace("KB", "")) * 1024)
    else:
        return int(size_str)

def monitor_input():
    processed_files = set()
    file_list = request_file_list()
    display_file_list(file_list)
    try:
        while True:
            with open("input.txt", "r") as f:
                files_to_download = set(line.strip() for line in f if line.strip())
                new_files = files_to_download - processed_files
            for file_name in new_files:
                file_map = {file.split()[0]: parse_size(file.split()[1]) for file in file_list}
                if file_name in file_map:
                    print(f"Starting download of {file_name}")
                    download_file(file_name, file_map[file_name])
                    display_file_list(file_list)
                else:
                    print(f"File {file_name} not found on server")
                    display_file_list(file_list)
                processed_files.add(file_name)
                
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting monitor")

if __name__ == "__main__":
    monitor_input()
