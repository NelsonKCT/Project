import socket
import threading
MAX_CLIENT  = 5

def RegisterOrLogin(client):
    Letter  = client.recv(1024).decode().strip()
    if Letter == "R":
        #let client register an account
        client.sendall("Please Enter your Account:\n".encode())
        Account = client.recv(1024).decode().strip()
        client.sendall("Please Enter your Password:\n".encode())
        Password = client.recv(1024).decode().strip()
        client.sendall("Please Renter your Password:\n".encode())
        Password1 = client.recv(1024).decode().strip()
        if Password != Password1:
            client.sendall("Failed:\n".encode())

        
    elif Letter == "A":
        client.sendall("Please Enter your Account:\n".encode())
        client.sendall("Please Enter your Password:\n".encode())
    else:
        client.sendall("Invalid Input".encode())

    return
def handleClient(client):
    client.sendall("Welcome Enter R to register a Account or Enter A if you already have an account:P\n".encode())
    RegisterOrLogin(client)
    return
def serverThread():
    # TCP connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    serverIP = '127.0.0.1'
    port = 8888
    #binding
    try:
        server.bind((serverIP,port))
    except:
        print("server init failed")
        return
    #listen
    server.listen(MAX_CLIENT)
    while True:
        client,addr = server.accept()
        print(f"Client{addr} Connected\n")
        threading.Thread(target = handleClient,args = (client,)).start()



        

    
def main():
    ServerDown = False
    print("Server Starting ... ")
    #server background Thread
    threading.Thread(target = serverThread,daemon = True).start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server shutting down")
        return
if __name__ == "__main__":
    main()

