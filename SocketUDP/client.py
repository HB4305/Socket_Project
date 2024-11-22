import socket
import threading
import os
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 1024 * 1024  # Mỗi chunk 1MB

# Hàm tải về từng phần của file
def download_chunk(filename, offset, length, part_number):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # Gửi yêu cầu tải về file từ server
        sock.sendto(f"DOWNLOAD_REQUEST {filename} {offset} {length}".encode(), (SERVER_HOST, SERVER_PORT))
        
        with open(f"{filename}.part{part_number}", "wb") as f:
            total_received = 0  # Tổng số byte đã nhận
            while total_received < length:  # Chỉ tiếp tục nếu còn byte cần nhận
                remaining_bytes = length - total_received
                data, _ = sock.recvfrom(min(CHUNK_SIZE, remaining_bytes))  # Nhận tối đa chunk size hoặc byte còn lại
                if not data:  # Nếu không có dữ liệu nữa, dừng
                    print(f"Error: No more data received for part {part_number} of {filename}")
                    break
                f.write(data)  # Ghi dữ liệu vào file
                total_received += len(data)  # Cập nhật tổng số byte đã nhận
                progress = total_received / length * 100  # Tính tiến độ
                print(f"Downloading {filename} part {part_number} .... {progress:.2f}%")

# Hàm tải về file, chia thành các phần và tải song song
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
            with open(f"{filename}.part{part}", "rb") as f:
                final_file.write(f.read())
            os.remove(f"{filename}.part{part}")


# Hàm giám sát input từ file và tải file
def monitor_input():
    processed_files = set()
    while True:
        with open("C:/Users/ADMIN/Documents/GitHub/Socket_Project/SocketUDP/input.txt", "r") as f:
            files_to_download = set(line.strip() for line in f if line.strip())
        new_files = files_to_download - processed_files
        for filename in new_files:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # Gửi yêu cầu để nhận danh sách file từ server
                sock.sendto("LIST_FILES".encode(), (SERVER_HOST, SERVER_PORT))
                file_list, _ = sock.recvfrom(4096)  # Nhận dữ liệu danh sách file
                file_list = file_list.decode().splitlines()
                file_map = {line.split()[0]: int(line.split()[1].replace("MB", "")) * 1024 * 1024 for line in file_list}
                
                # Kiểm tra xem file có tồn tại trên server không
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
