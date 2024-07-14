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

    # server_ip = addresServer
    server_ip = 'localhost'
    server_port = 8484

    #Cria vinculo do socket com o IP e a porta
    serverSocket.bind((server_ip, server_port))     
    print("---------------- Server started! ---------")  
    print("Listening on IP: ", server_ip, " Port: ", str(server_port))

    #Recebe um ping do cliente e devolve o Echo
    while True:
        data, client_address = serverSocket.recvfrom(buffer_size)
        decode_data = data.decode("utf-8")
        print("Echo data: ", decode_data, "from: ", client_address)
        
        sent = serverSocket.sendto(data, client_address)
        print("Sent: ", decode_data, "to: ", client_address)
        
        if decode_data == "CLOSE":
            print("Server closed")
            break
except Exception as e:
    print("Error: ", e)
finally:
    serverSocket.close()
