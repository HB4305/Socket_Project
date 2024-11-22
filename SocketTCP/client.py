import socket
import threading
import os
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 1024 * 1024  # Mỗi chunk 1MB

def download_chunk(filename, offset, length, part_number):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER_HOST, SERVER_PORT))
        sock.send(f"DOWNLOAD_REQUEST {filename} {offset} {length}".encode())
    with open(f"{filename}.part{part_number}", "wb") as f:
        total_received = 0  # Tổng số byte đã nhận
    while total_received < length:  # Chỉ tiếp tục nếu còn byte cần nhận
        remaining_bytes = length - total_received
        data = sock.recv(min(4096, remaining_bytes))  # Nhận tối đa 4096 hoặc số byte còn lại
        if not data:  # Nếu không có dữ liệu nữa, dừng
            break
        f.write(data)  # Ghi dữ liệu vào file
        total_received += len(data)  # Cập nhật tổng số byte đã nhận
        progress = total_received / length * 100  # Tính tiến độ
        print(f"Downloading {filename} part {part_number} .... {progress:.2f}%")

def download_file(filename, file_size):
    chunk_length = file_size // 4
    threads = []
    for part in range(4):
        offset = part * chunk_length
        length = chunk_length if part < 3 else file_size - offset
        thread = threading.Thread(target=download_chunk, args=(filename, offset, length, part + 1))
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()

    # Ghép các file part thành file hoàn chỉnh
    with open(filename, "wb") as final_file:
        for part in range(1, 5):
            part_filename = f"{filename}.part{part}"
            with open(part_filename, "rb") as part_file:
                final_file.write(part_file.read())
            os.remove(part_filename)  # Xóa file part sau khi ghép

def monitor_input():
    processed_files = set()
    while True:
        with open("input.txt", "r") as f:
            files_to_download = set(line.strip() for line in f if line.strip())
        new_files = files_to_download - processed_files
        for filename in new_files:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((SERVER_HOST, SERVER_PORT))
                sock.send("LIST_FILES".encode())
                file_list = sock.recv(4096).decode().splitlines()
                file_map = {line.split()[0]: int(line.split()[1].replace("MB", "")) * 1024 * 1024 for line in file_list}
                
                if filename in file_map:
                    print(f"Starting download of {filename}")
                    download_file(filename, file_map[filename])
                    print(f"Completed download of {filename}")
                else:
                    print(f"File {filename} not found on server")
            processed_files.add(filename)
        time.sleep(5)

if __name__ == "__main__":
    monitor_input()
