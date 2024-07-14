import socket

try:
    buffer_size = 1500
    
    #Criação do server
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #connect() apenas para pegar o IP da máquina
    s.connect(('8.8.8.8', 1))
    addresServer = s.getsockname()[0]
    s.close()

    server_ip = addresServer
    server_port = 8000

    #Cria vinculo do socket com o IP e a porta
    serverSocket.bind((server_ip, server_port))     
    print("---------------- Server started! ---------")  
    print("Listening on IP: ", server_ip, " Port: ", str(server_port))

    while True:
        data, address = serverSocket.recvfrom(buffer_size)
        print("received message: ", data, "from: ", address)

except Exception as e:
    print("Error: ", e)

