#client
import socket
import threading
from sys import stdout
import sys
import time
import logging
import subprocess

#SERVER_IP = "localhost"#192.168.15.200
SERVER_IP = "192.168.15.200"
UDP_PORT = 4000
TCP_PORT = 4001
NEW_TCP_PORT = 4002
BUFFER_SIZE = 1400
BUFFER_VIDEO = bytearray()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
id_lock = threading.Lock()

def process_video_data():
    #time.sleep(0.005)
    global BUFFER_VIDEO
    try:
        new_tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_tcp_sock.connect((SERVER_IP, TCP_PORT))
    except Exception as e:
        logging.error(f"Error in connecting TCP: {e}")
    logging.info("chegou no process video")

    process = subprocess.Popen(
        ['mpv', '--no-cache', '--no-input-default-bindings', '-'],  # '-' indica stdin
        stdin=subprocess.PIPE
    )

    while True:
        time.sleep(0.05)
        if len(BUFFER_VIDEO) >= 28000 and (len(BUFFER_VIDEO)%1400==0):
            with id_lock:
                aux = BUFFER_VIDEO
                BUFFER_VIDEO = bytearray()
            try:
                for i in range(0, len(aux), 3*BUFFER_SIZE):
                    #stdout.buffer.write(aux[i:i+3*BUFFER_SIZE])
                    #sys.stdout.buffer.flush()
                    process.stdin.write(aux[i:i+3*BUFFER_SIZE])

                new_tcp_sock.send(b'NEXT')
            except Exception as e:
                logging.error(f"Error processing video data: {e}")
        if (len(BUFFER_VIDEO) > 0) and (len(BUFFER_VIDEO)%1400!=0):
            with id_lock:
                aux = BUFFER_VIDEO
                BUFFER_VIDEO = bytearray()
            try:
                for i in range(0, len(aux), BUFFER_SIZE):
                    stdout.buffer.write(aux[i:i+BUFFER_SIZE])
                    sys.stdout.buffer.flush()
                new_tcp_sock.send(b'END')
                process.stdin.close()
                # Esperar o processo do MPV terminar
                process.wait()
                logging.info("fim do video")
                break

            except Exception as e:
                logging.error(f"Error processing video data: {e}")

def receive_udp_stream():
    global BUFFER_VIDEO
    #logging.info("chegou aqui 1")
    try:
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (SERVER_IP, UDP_PORT)
        time.sleep(0.5)
        udp_sock.sendto(b'ola', address)
        #logging.info("chegou aqui 2")
        id = 0
        video_data = bytearray()
        while True:
            #logging.info("esperando pacote")
            data, _ = udp_sock.recvfrom(BUFFER_SIZE)
            id += 1
            video_data += data + b''
            #logging.info("chegou aqui 1")
            if id > 35 or not data:
                with id_lock:
                    BUFFER_VIDEO += video_data
                video_data = bytearray()
                id = 0
            if not data:
                break
        udp_sock.close()
    except Exception as e:
        logging.error(f"Error in streaming the video: {e}")
    finally:
        udp_sock.close()
        return


def seek_control():
    try:
        seek_tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        seek_tcp_sock.connect((SERVER_IP, NEW_TCP_PORT))
        logging.info("Conexão de controle TCP estabelecida.")

        while True:#p: pausar, c: continuar, s: sair
            command = input()
            seek_tcp_sock.send(command.encode())
            if command == "STOP":
                break
    finally:
        seek_tcp_sock.close()

if __name__ == "__main__":
    #try:

    add = input()
    UDP_PORT += int(add)
    TCP_PORT += int(add)
    NEW_TCP_PORT += int(add)
    #send_tcp_control()
    
    seek_thread = threading.Thread(target=seek_control)
    #seek_thread.daemon = True
    seek_thread.start()

    try:

        udp_thread = threading.Thread(target=receive_udp_stream)
        udp_thread.daemon = True
        udp_thread.start()

        video_data_thread = threading.Thread(target=process_video_data)
        video_data_thread.start()

        udp_thread.join()
        video_data_thread.join()

        #seek_thread.join()
    except Exception as e:
        logging.error(f"Error creating UDP thread: {e}")
    
    #finally:
        #new_tcp_sock.close()