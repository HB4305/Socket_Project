import socket
import struct
import time

CHUNK_SIZE = 1024
PORT = 8080
SERVER_IP = "127.0.0.1"
INPUT_FILE = "C:/Users/ADMIN/Documents/GitHub/Socket_Project/SocketUDP/input.txt"

def get_server_files(client_socket):
    client_socket.sendto(b"LIST", (SERVER_IP, PORT))
    data, _ = client_socket.recvfrom(4096)
    return data.decode().splitlines()

def download_file(client_socket, filename):
    client_socket.sendto(f"GET {filename}".encode(), (SERVER_IP, PORT))

    file_data = {}
    expected_sequence = 0

    print(f"Downloading file: {filename}")

    while True:
        packet, _ = client_socket.recvfrom(CHUNK_SIZE + 4)
        sequence_number = struct.unpack("I", packet[:4])[0]
        chunk = packet[4:]

        if sequence_number == expected_sequence:
            file_data[sequence_number] = chunk
            ack_packet = struct.pack("I", sequence_number)
            client_socket.sendto(ack_packet, (SERVER_IP, PORT))
            expected_sequence += 1

        if len(chunk) < CHUNK_SIZE:
            break

    with open(filename, "wb") as f:
        for i in range(len(file_data)):
            f.write(file_data[i])

    print(f"File {filename} downloaded successfully.")

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    downloaded_files = set()

    while True:
        try:
            # Đọc danh sách file từ server
            server_files = get_server_files(client_socket)

            # Đọc danh sách file từ input.txt
            with open(INPUT_FILE, "r") as f:
                input_files = [line.strip() for line in f.readlines()]

            # Kiểm tra file nào cần tải
            for file in input_files:
                if file not in downloaded_files and file in server_files:
                    download_file(client_socket, file)
                    downloaded_files.add(file)

            time.sleep(5)  # Chờ 5 giây trước khi kiểm tra lại
        except FileNotFoundError:
            print(f"File {INPUT_FILE} not found!")
            time.sleep(5)

if __name__ == "__main__":
    main()
