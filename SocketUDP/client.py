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
    percent = min(100, percent)
    filled_length = int(length * iteration // total)
    bar = '#' * filled_length + '-' * (length - filled_length)
    sys.stdout.write(f'\r|{bar}| {percent:.1f}% Complete')
    sys.stdout.flush()

def download_file(filename, file_size):
    """Tải toàn bộ file mà không cần chia thành phần nhỏ."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(f"DOWNLOAD_REQUEST {filename}".encode(), (SERVER_HOST, SERVER_PORT))
    with open(filename, "wb") as f:
        total_received = 0  # Tổng số byte đã nhận
        expected_seq = 0  # Sequence number bắt đầu từ 0
        while True:
            data, _ = sock.recvfrom(CHUNK_SIZE + 42)  # 42 byte là 8 byte cho sequence number, 1 byte cho khoảng trắng, và 33 byte cho hash value
            if data == b"End":
                break

            seq = int(data[:8])
            hash_value, chunk_data = data[9:41], data[42:]
            if seq == expected_seq and hashlib.md5(chunk_data).hexdigest().encode() == hash_value:
                f.write(chunk_data)
                total_received += len(chunk_data)
                print_progress_bar(total_received, file_size)
                sock.sendto(f"ACK {seq}".encode(), (SERVER_HOST, SERVER_PORT))  # Gửi ACK cho server
                expected_seq += 1
            else:
                sock.sendto(f"NACK {expected_seq}".encode(), (SERVER_HOST, SERVER_PORT))  # Gửi NACK cho server
    sock.close()  # Đóng socket sau khi tải xong
    print()  # In dòng mới để kết thúc progress bar

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
            for filename in new_files:
                file_map = {file.split()[0]: parse_size(file.split()[1]) for file in file_list}
                if filename in file_map:
                    print(f"Starting download of {filename}")
                    download_file(filename, file_map[filename])
                    print(f"Download of {filename} complete")
                    display_file_list(file_list)
                else:
                    print(f"File {filename} not found on server")
                    display_file_list(file_list)
                processed_files.add(filename)
                
            time.sleep(5)
    except KeyboardInterrupt:
        print("Exiting monitor")

if __name__ == "__main__":
    monitor_input()
