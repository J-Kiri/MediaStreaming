import socket

try:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    s.connect(('8.8.8.8', 1))
    addresServer = s.getsockname()[0]

    print(addresServer)

    server_ip = "127.0.0.1"
    server_port = 8000

    serverSocket.bind((server_ip, server_port)) 
except Exception as e:
    print("Error: ", e)
    
    