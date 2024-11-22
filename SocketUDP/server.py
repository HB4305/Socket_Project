import socket
import struct
import threading

CHUNK_SIZE = 1024
PORT = 8080
SERVER_IP = "127.0.0.1"
FILES_LIST = "C:/Users/ADMIN/Documents/GitHub/Socket_Project/SocketUDP/files.txt"  # Danh sách file có sẵn

def send_file_chunk(filename, client_address, server_socket):
    try:
        with open(filename, "rb") as file:
            sequence_number = 0
            while True:
                chunk = file.read(CHUNK_SIZE)
                if not chunk:
                    break

                # Đóng gói chunk với số thứ tự
                packet = struct.pack("I", sequence_number) + chunk

                while True:
                    server_socket.sendto(packet, client_address)

                    # Chờ ACK
                    try:
                        server_socket.settimeout(2)
                        ack_packet, _ = server_socket.recvfrom(1024)
                        ack_number = struct.unpack("I", ack_packet)[0]

                        if ack_number == sequence_number:
                            break
                    except socket.timeout:
                        continue

                sequence_number += 1
    except FileNotFoundError:
        server_socket.sendto(b"ERROR: File not found!", client_address)

def handle_request(data, client_address, server_socket):
    request_type, *args = data.decode().split()

    if request_type == "LIST":
        # Gửi danh sách file về client
        try:
            with open(FILES_LIST, "r") as f:
                files = f.read()
            server_socket.sendto(files.encode(), client_address)
        except FileNotFoundError:
            server_socket.sendto(b"ERROR: No files available!", client_address)

    elif request_type == "GET":
        filename = args[0]
        threading.Thread(target=send_file_chunk, args=(filename, client_address, server_socket)).start()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, PORT))
    print("Server is running...")

    while True:
        data, client_address = server_socket.recvfrom(1024)
        threading.Thread(target=handle_request, args=(data, client_address, server_socket)).start()

if __name__ == "__main__":
    main()
