import socket
import threading
import os
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 1024 * 1024  # Mỗi chunk 1MB

def download_chunk(filename, offset, length, part_number):
    # Tạo socket ở ngoài với block 'with', để giữ socket mở trong suốt quá trình tải
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((SERVER_HOST, SERVER_PORT))
    sock.send(f"DOWNLOAD_REQUEST {filename} {offset} {length}".encode())

    with open(f"{filename}.part{part_number}", "wb") as f:
        total_received = 0  # Tổng số byte đã nhận

        while total_received < length:  # Chỉ tiếp tục nếu còn byte cần nhận
            remaining_bytes = length - total_received
            data = sock.recv(min(1024, remaining_bytes))  # Nhận tối đa 1024 byte hoặc số byte còn lại
            if not data:  # Nếu không có dữ liệu nữa, dừng
                break
            f.write(data)  # Ghi dữ liệu vào file
            total_received += len(data)  # Cập nhật tổng số byte đã nhận
            progress = total_received / length * 100  # Tính tiến độ
            print(f"Downloading {filename} part {part_number} .... {progress:.2f}%")
    
    sock.close()  # Đóng socket sau khi tải xong


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

def format_size(size_in_bytes):
    """Chuyển đổi kích thước từ byte sang GB, MB hoặc B, chỉ hiển thị phần thập phân khi cần."""
    if size_in_bytes >= 1024 * 1024 * 1024:
        size_in_gb = size_in_bytes / (1024 * 1024 * 1024)
        return f"{int(size_in_gb)} GB" if size_in_gb.is_integer() else f"{size_in_gb:.2f} GB"
    elif size_in_bytes >= 1024 * 1024:
        size_in_mb = size_in_bytes / (1024 * 1024)
        return f"{int(size_in_mb)} MB" if size_in_mb.is_integer() else f"{size_in_mb:.2f} MB"
    elif size_in_bytes >= 1024:
        size_in_kb = size_in_bytes / 1024
        return f"{int(size_in_kb)} KB" if size_in_kb.is_integer() else f"{size_in_kb:.2f} KB"
    else:
        return f"{size_in_bytes} B"

def monitor_input():
    processed_files = set()

    # Tải danh sách tệp từ server một lần
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER_HOST, SERVER_PORT))
        sock.send("LIST_FILES".encode())
        data = sock.recv(4096).decode()
        file_list = data.splitlines()
        file_map = {
            line.split()[0]: int(line.split()[1].replace("GB", "")) * 1024 * 1024 * 1024
            if "GB" in line
            else int(line.split()[1].replace("MB", "")) * 1024 * 1024
            if "MB" in line
            else int(line.split()[1].replace("B", ""))
            for line in file_list
        }

    print("Available files:")
    for filename, size in file_map.items():
        print(f"- {filename}: {format_size(size)}")

    while True:
        with open("input.txt", "r") as f:
            # Đọc danh sách tệp cần tải từ input.txt
            files_to_download = set(line.strip() for line in f if line.strip())
        
        # Lấy các tệp mới cần tải
        new_files = files_to_download - processed_files

        for filename in new_files:
            if filename in file_map:
                download_file(filename, file_map[filename])
            else:
                print(f"File {filename} not found on server")
            processed_files.add(filename)

        time.sleep(5)

if __name__ == "__main__":
    monitor_input()