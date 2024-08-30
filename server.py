import socket
import time
from contextlib import closing
import logging
import queue
import threading

# OWN_IP define o endereço IP local da máquina que executa o servidor. Aqui está configurado para 'localhost', mas pode ser substituído pelo IP apropriado.
# UDP_PORT é a porta utilizada para comunicação via UDP.
# TCP_PORT é a porta utilizada para comunicação via TCP.
# BUFFER_SIZE define o tamanho do buffer para leitura dos dados do vídeo.

OWN_IP = "localhost"
UDP_PORT = 5005
TCP_PORT = 5006
NEW_TCP_PORT = 5007
BUFFER_SIZE = 1400

ROLLBACK_SECONDS = 10

control_queue = queue.Queue()

# Configuração básica de logging para registrar informações, erros e mensagens importantes do servidor.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Função responsável por enviar o vídeo via UDP. Recebe o socket UDP, a conexão TCP, e o endereço do cliente.
def handle_udp_streaming(udp_sock, tcp_conn, addr):
    logging.info("UDP Server Ready to send data...")

    id = 0  # Contador de pacotes enviados.
    total = 0  # Total de dados enviados em MB.

    # Abrindo o arquivo de vídeo em modo binário para leitura.
    with open('foguete.mp4', 'rb') as video_file:
        while True:
            try: 
                if not control_queue.empty():
                    command = control_queue.get()

                    if(command == ord('p')):
                        logging.info("Streaming pausado.")
                        while control_queue.get() != ord('c'):
                            pass
                        logging.info("Streaming retomado.")
                    elif(command == ord('s')):
                        logging.info("Streaming interrompido.")
                        break
                    elif(command == ord('r')):
                        position_return = video_file.tell() - (ROLLBACK_SECONDS * BUFFER_SIZE)
                        video_file.seek(position_return)
                        
                # Leitura de um pedaço do arquivo de vídeo com tamanho definido pelo BUFFER_SIZE.
                data = video_file.read(BUFFER_SIZE)
                if not data:
                    # Se não houver mais dados para ler, significa que o vídeo terminou.
                    logging.info("End of video file")
                    udp_sock.sendto(b'', addr)  # Envia um pacote vazio para indicar o fim do vídeo.
                    return
               
                try:
                    id += 1
                    total += len(data)  # Calcula o total de dados enviados em KB.
                    udp_sock.sendto(data, addr)  # Envia o pacote UDP com os dados do vídeo.
                    logging.info(f"Sent {id} packets with {len(data)} bytes to {addr}, total sent: {total}B")
                    time.sleep(0.0005)  # Pequena pausa para evitar congestionamento.
                except Exception as e:
                    logging.error(f"Error in transmitting the video: {e}")

                # A cada 10 pacotes, o servidor espera uma resposta do cliente via TCP.
                if id == 10:
                    control_data = tcp_conn.recv(BUFFER_SIZE).decode()
                    # print(f"Received from client: {control_data}")
                    if control_data != "NEXT":
                        break  # Se a resposta não for "NEXT", interrompe o envio.
                    id = 0  # Reseta o contador de pacotes.

            except Exception as e:
                logging.error(f"Error sending UDP data: {e}")
                break

    return

# Função responsável por estabelecer a conexão TCP com o cliente.
def handle_tcp_control(tcp_sock):
    try:
        tcp_sock.listen(1)  # Coloca o socket TCP em modo de escuta para aceitar conexões.
        conn, addr = tcp_sock.accept()  # Aceita a conexão TCP do cliente.
        print(f"TCP connection established with {addr}")
        return conn, addr  # Retorna o objeto da conexão e o endereço do cliente.
    except Exception as e:
        logging.error(f"Error establishing TCP connection: {e}")

def seek_control():
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind((OWN_IP, NEW_TCP_PORT))
    tcp_sock.listen(1)
    conn, addr = tcp_sock.accept()
    print(f"Conexão de controle estabelecida com {addr}")

    while True:
        command = conn.recv(BUFFER_SIZE).decode()
        if not command:
            break
        print(f"Comando recebido: {command}")
        control_queue.put(ord(command))

    conn.close()
    tcp_sock.close()


# Função para encontrar uma porta livre no sistema, caso UDP_PORT ou TCP_PORT não sejam definidos.
def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))  # Liga o socket a uma porta livre.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]  # Retorna o número da porta livre.

# Bloco principal do código, executado quando o script é iniciado.
if __name__ == "__main__":
    if(UDP_PORT and TCP_PORT == 0):
        # Se as portas não forem definidas, encontra portas livres automaticamente.
        UDP_PORT = find_free_port()
        TCP_PORT = find_free_port()
        print("UDP PORT =", UDP_PORT)
        print("TCP PORT =", TCP_PORT)

    seek_thread = threading.Thread(target=seek_control)
    seek_thread.start()

    try:
        # Cria o socket TCP e faz a ligação com o endereço e porta definidos.
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.bind((OWN_IP, TCP_PORT))
        tcp_conn, tcp_addr = handle_tcp_control(tcp_sock)
    except Exception as e:
        logging.error(f"Error binding TCP: {e}") 

    try:
        # Cria o socket UDP e faz a ligação com o endereço e porta definidos.
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        udp_sock.bind((OWN_IP, UDP_PORT))
        _, addr = udp_sock.recvfrom(10)  # Espera uma mensagem inicial do cliente para obter o endereço.
    except Exception as e:
        logging.error(f"Error binding UDP: {e}")

    # Inicia o envio dos dados de vídeo via UDP.
    handle_udp_streaming(udp_sock, tcp_conn, addr)

    # Fecha as conexões TCP e UDP ao final da transmissão.
    tcp_conn.close()
    tcp_sock.close()
    print("Server closed")
