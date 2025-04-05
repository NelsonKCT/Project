import socket
import threading 
import sympy
import json
from Message import createMessage
from HandleClient import HandleClient
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.port = port
        self.MAX_CLIENT = 5
    def serverThread(self):
        try:
            self.server.bind((self.ip, self.port))
        except :
            print("server init failed")
            return
        #listen
        self.server.listen(self.MAX_CLIENT)
        while True:
            try:
                client,addr = self.server.accept()
                client.sendall(createMessage("info","hi", False))
                newClient = HandleClient(client, addr)
                threading.Thread(target = newClient.handleClient).start()
            except ConnectionResetError:
                print(f"Client{addr} Disconnected\n")