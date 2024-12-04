import socket
import threading
import os
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 4096  # Mỗi chunk 4096 byte

# Lưu trạng thái tiến trình tải của các phần
progress_status = {}

def download_chunk(filename, offset, length, part_number):
    """Tải một phần (chunk) của file."""
    global progress_status
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(f"DOWNLOAD_REQUEST {filename} {offset} {length}".encode(), (SERVER_HOST, SERVER_PORT))

    with open(f"{filename}.part{part_number}", "wb") as f:
        total_received = 0  # Tổng số byte đã nhận
        while True:
            data, _ = sock.recvfrom(CHUNK_SIZE)  # Nhận 4096 byte
            if data == b"End":
                break
            for i in range(0, len(data), 64):  # Xử lý từng phần nhỏ 1024 byte
                f.write(data[i:i+64])
                total_received += len(data[i:i+64])
                progress_status[part_number] = (total_received) / length * 100  # Cập nhật tiến trình

    sock.close()  # Đóng socket sau khi tải xong


def display_progress(filename, num_parts):
    """Hiển thị tiến trình tải."""
    while any(progress < 100 for progress in progress_status.values()):
        os.system('cls' if os.name == 'nt' else 'clear')  # Xóa màn hình
        print(f"Downloading {filename}:")
        for part in range(1, num_parts + 1):
            progress = progress_status.get(part, 0)
            print(f"Downloading {filename} part {part} .... {progress:.2f}%")
        time.sleep(0.03)


def download_file(filename, file_size):
    """Tải một file chia thành nhiều phần."""
    global progress_status
    num_parts = 4  # Số phần chia
    chunk_length = file_size // num_parts
    threads = []

    # Khởi tạo tiến trình hiển thị tiến trình tải
    progress_status = {part: 0 for part in range(1, num_parts + 1)}
    progress_thread = threading.Thread(target=display_progress, args=(filename, num_parts))
    progress_thread.start()

    # Khởi động các thread tải dữ liệu song song
    for part in range(num_parts):
        offset = part * chunk_length
        length = chunk_length if part < num_parts - 1 else file_size - offset
        thread = threading.Thread(target=download_chunk, args=(filename, offset, length, part + 1))
        thread.start()
        threads.append(thread)

    # Chờ tất cả các thread tải dữ liệu hoàn thành
    for t in threads:
        t.join()

    progress_thread.join()  # Kết thúc tiến trình hiển thị

    # Ghép các file part thành file hoàn chỉnh
    with open(filename, "wb") as final_file:
        for part in range(1, num_parts + 1):
            part_filename = f"{filename}.part{part}"
            with open(part_filename, "rb") as part_file:
                final_file.write(part_file.read())
            os.remove(part_filename)  # Xóa file part sau khi ghép


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
        print(file)

def monitor_input():
    """Theo dõi file `input.txt` để tải các file được liệt kê."""
    processed_files = set()
    file_list = request_file_list()
    display_file_list(file_list)
    while True:
        with open("input.txt", "r") as f:
            files_to_download = set(line.strip() for line in f if line.strip())
            new_files = files_to_download - processed_files
        for filename in new_files:
            file_map = {line.split()[0]: int(line.split()[1].replace("MB", "")) * 1024 * 1024 for line in file_list}
            if filename in file_map:
                print(f"Starting download of {filename}")
                download_file(filename, file_map[filename])
                print(f"Completed download of {filename}")
            else:
                print(f"File {filename} not found on server")
            processed_files.add(filename)
            file_list = request_file_list()
            display_file_list(file_list)
        time.sleep(5)


if __name__ == "__main__":
    monitor_input()
