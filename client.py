import socket
import threading
from sys import stdout
import sys
import logging

SERVER_IP = "localhost"
UDP_PORT = 5005
TCP_PORT = 5006
NEW_TCP_PORT = 5007
BUFFER_SIZE = 1400
TOL = 0.1

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
id_lock = threading.Lock()

def process_video_data(video_data):
    try:
        for i in range(0, len(video_data), BUFFER_SIZE):
            stdout.buffer.write(video_data[i:i+BUFFER_SIZE])
            sys.stdout.buffer.flush()
        tcp_sock.send(b'NEXT')
    except Exception as e:
        logging.error(f"Error processing video data: {e}")

def receive_udp_stream():
    try:
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (SERVER_IP, UDP_PORT)
        udp_sock.sendto(b'ola', address)
        
        id = 0
        video_data = bytearray()

        while True:
            data, _ = udp_sock.recvfrom(BUFFER_SIZE)
            if not data:
                break

            video_data += data
            id += 1        

            if id >= 10*(1-TOL):
                video_data_thread = threading.Thread(target=process_video_data, args=(video_data,))
                video_data_thread.start()

                with id_lock:
                    id = 0
                    video_data = bytearray()
            
        udp_sock.close()
    except Exception as e:
        logging.error(f"Error in streaming the video: {e}")

def send_tcp_control():
    try:
        global tcp_sock
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, TCP_PORT))
    except Exception as e:
        logging.error(f"Error in connecting TCP: {e}")

# def seek_control():
#     try:
#         tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         tcp_sock.connect((SERVER_IP, NEW_TCP_PORT))
#         logging.info("Conexão de controle TCP estabelecida.")

#         while True:#p: pausar, c: continuar, s: sair
#             command = input()
#             tcp_sock.send(command.encode())
#             if command == "STOP":
#                 break

#     finally:
#         tcp_sock.close()

if __name__ == "__main__":
    try:
        send_tcp_control()
        
        # seek_thread = threading.Thread(target=seek_control)
        # seek_thread.start()

        try:
            udp_thread = threading.Thread(target=receive_udp_stream)
            udp_thread.start()
            udp_thread.join()
        except Exception as e:
            logging.error(f"Error creating UDP thread: {e}")
    finally:
        tcp_sock.close()


