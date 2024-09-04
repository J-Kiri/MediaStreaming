#server
import socket
import time
from contextlib import closing
import logging
import queue
import threading

OWN_IP = "localhost"
UDP_PORT = 5005
TCP_PORT = 5006
NEW_TCP_PORT = 5007
BUFFER_SIZE = 1400

ROLLBACK_SECONDS = 5

control_queue = queue.Queue()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def handle_udp_streaming(udp_sock, tcp_conn, addr):
    id = 0
    total = 0

    with open('foguete.mp4', 'rb') as video_file:
        
            try:
                while True:
                    if not control_queue.empty():
                        command = control_queue.get()
                        if command == "p":
                            logging.info("Streaming pausado.")
                            while control_queue.get() != "c":
                                pass
                            logging.info("Streaming retomado.")
                        elif command == "s":
                            logging.info("Streaming interrompido.")
                            break
                        elif command == "rw":
                            logging.info("Rewinding video by 5 seconds")
                            video_file.seek(video_file.tell() - ROLLBACK_SECONDS * BUFFER_SIZE)
                        elif command == "fw":
                            logging.info("Forwarding video by 5 seconds")
                            video_file.seek(video_file.tell() + ROLLBACK_SECONDS * BUFFER_SIZE)
                    
                    
                    data = video_file.read(BUFFER_SIZE)
                    if not data:
                        logging.info("End of video file")
                        udp_sock.sendto(b'', addr)
                        return
                
                    try:
                        id += 1
                        total += len(data)
                        udp_sock.sendto(data, addr)
                        logging.info(f"Sent to client: {total} B")
                        #time.sleep(0.0005)
                    except Exception as e:
                        logging.error(f"Error in transmitting the video: {e}")

                    if id >= 100:
                        control_data = tcp_conn.recv(BUFFER_SIZE).decode()
                        logging.info(f"Received from client: {control_data}")
                        if control_data != "NEXT":
                            break
                        id = 0 

            except Exception as e:
                logging.error(f"Error sending UDP data: {e}")
            finally:
                udp_sock.close()
    return

def handle_tcp_control(tcp_sock):
    try:
        tcp_sock.listen(1)
        conn, addr = tcp_sock.accept()
        logging.info(f"TCP connection established with {addr}")
        return conn, addr
    except Exception as e:
        logging.error(f"Error establishing TCP connection: {e}")

def seek_control():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((OWN_IP, NEW_TCP_PORT))
    tcp_sock.listen(1)
    conn, addr = tcp_sock.accept()
    logging.info(f"Conexão de controle estabelecida com {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode()
            if not data:
                break
            logging.info(f"Comando recebido: {data}")
            control_queue.put(data)

        conn.close()
        tcp_sock.close()
    except Exception as e:
        logging.error(f"Error sending UDP data: {e}")
    finally:
        conn.close()
        tcp_sock.close()


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
    
if __name__ == "__main__":
    try:
        if(UDP_PORT and TCP_PORT == 0):
            UDP_PORT = find_free_port()
            TCP_PORT = find_free_port()
            logging.info("UDP PORT =", UDP_PORT)
            logging.info("TCP PORT =", TCP_PORT)

        seek_thread = threading.Thread(target=seek_control)
        seek_thread.start()

        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.bind((OWN_IP, TCP_PORT))
            tcp_conn, tcp_addr = handle_tcp_control(tcp_sock)
        except Exception as e:
            logging.error(f"Error binding TCP: {e}") 

        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
            udp_sock.bind((OWN_IP, UDP_PORT))
            _, addr = udp_sock.recvfrom(10)
        except Exception as e:
            logging.error(f"Error binding UDP: {e}")

        handle_udp_streaming(udp_sock, tcp_conn, addr)

    finally:
        tcp_conn.close()
        tcp_sock.close()
        logging.info("Server closed")