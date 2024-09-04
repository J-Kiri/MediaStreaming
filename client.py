#client
import socket
import threading
from sys import stdout
import sys
import time
import logging

SERVER_IP = "localhost"
UDP_PORT = 5005
TCP_PORT = 5006
NEW_TCP_PORT = 5007
BUFFER_SIZE = 1400
BUFFER_VIDEO = bytearray()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
id_lock = threading.Lock()

def process_video_data():
    #time.sleep(0.05)
    global BUFFER_VIDEO
    while True:
        if len(BUFFER_VIDEO) >= 28000:
            with id_lock:
                aux = BUFFER_VIDEO
                BUFFER_VIDEO = bytearray()
            try:
                for i in range(0, len(aux), BUFFER_SIZE):
                    stdout.buffer.write(aux[i:i+BUFFER_SIZE])
                    sys.stdout.buffer.flush()
                tcp_sock.send(b'NEXT')
            except Exception as e:
                logging.error(f"Error processing video data: {e}")
        elif (len(BUFFER_VIDEO) > 0) and (len(BUFFER_VIDEO)%1400!=0):
            with id_lock:
                aux = BUFFER_VIDEO
                BUFFER_VIDEO = bytearray()
            try:
                for i in range(0, len(aux), BUFFER_SIZE):
                    stdout.buffer.write(aux[i:i+BUFFER_SIZE])
                    sys.stdout.buffer.flush()
                tcp_sock.send(b'END')
            except Exception as e:
                logging.error(f"Error processing video data: {e}")

def receive_udp_stream():
    global BUFFER_VIDEO
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
            id += 1
            video_data += data
            #logging.info("chegou aqui 1")
            if id > 80 or not data:
                with id_lock:
                    BUFFER_VIDEO += video_data
                video_data = bytearray()
                id = 0
        udp_sock.close()
    except Exception as e:
        logging.error(f"Error in streaming the video: {e}")
    finally:
        udp_sock.close()
        return

def send_tcp_control():
    try:
        global tcp_sock
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, TCP_PORT))
    except Exception as e:
        logging.error(f"Error in connecting TCP: {e}")


def seek_control():
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, NEW_TCP_PORT))
        logging.info("Conexão de controle TCP estabelecida.")

        while True:#p: pausar, c: continuar, s: sair
            command = input()
            tcp_sock.send(command.encode())
            if command == "STOP":
                break
    finally:
        tcp_sock.close()

if __name__ == "__main__":
    try:
        send_tcp_control()
        
        seek_thread = threading.Thread(target=seek_control)
        seek_thread.start()

        try:

            udp_thread = threading.Thread(target=receive_udp_stream)
            udp_thread.start()

            video_data_thread = threading.Thread(target=process_video_data)
            video_data_thread.start()

            udp_thread.join()
        except Exception as e:
            logging.error(f"Error creating UDP thread: {e}")
    finally:
        tcp_sock.close()


