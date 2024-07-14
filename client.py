import socket

try:
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_ip = 'localhost'
    server_port = 8484

    address = (server_ip, server_port)
    while True:
        message = input()
        byte_message = message.encode(encoding="utf-8")
        clientSocket.sendto(byte_message, address)
        
        data, server = clientSocket.recvfrom(1500)
        print("Received from ", server_ip, ": ", data.decode(encoding="utf-8"))

        if message == "CLOSE":
            print("Client closed.")
            break
except Exception as e:
    print("Error: ", e)
finally:
    clientSocket.close()