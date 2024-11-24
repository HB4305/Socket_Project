import socket
import threading
import os
import time

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 12345
CHUNK_SIZE = 1024

def download_chunk(filename, offset, length, part_number):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((SERVER_HOST, SERVER_PORT))

    # Gửi yêu cầu tải chunk
    sock.sendto(f"DOWNLOAD_REQUEST {filename} {offset} {length}".encode(), (SERVER_HOST, SERVER_PORT))

    with open(f"{filename}.part{part_number}", "wb") as f:
        total_received = 0
        expected_seq = 0  # Số thứ tự của chunk

        while total_received < length:
            remaining_bytes = length - total_received
            try:
                sock.settimeout(1)  # Thời gian chờ
                data, _ = sock.recvfrom(min(1024, remaining_bytes))  # Nhận dữ liệu

                # Kiểm tra số thứ tự gói tin
                seq_number = int(data.decode().split()[0])

                if seq_number == expected_seq:
                    chunk_data = sock.recvfrom(min(1024, remaining_bytes))[0]
                    f.write(chunk_data)
                    total_received += len(chunk_data)
                    expected_seq += 1

                    # Gửi ACK cho server
                    sock.sendto(f"ACK_{expected_seq - 1}".encode(), (SERVER_HOST, SERVER_PORT))
                else:
                    print(f"Received out of order chunk {seq_number}, expected {expected_seq}. Resending ACK...")
                    sock.sendto(f"NACK_{expected_seq}".encode(), (SERVER_HOST, SERVER_PORT))

            except socket.timeout:
                print(f"Timeout waiting for chunk {expected_seq}, retrying...")
                sock.sendto(f"NACK_{expected_seq}".encode(), (SERVER_HOST, SERVER_PORT))

    sock.close()

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
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((SERVER_HOST, SERVER_PORT))
                sock.sendto("LIST_FILES".encode(), (SERVER_HOST, SERVER_PORT))
                file_list, _ = sock.recvfrom(4096)
                file_list = file_list.decode().splitlines()

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
