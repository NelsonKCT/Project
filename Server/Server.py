import socket
import threading 
import sympy
import json
import logging
from Message import createMessage
from HandleClient import HandleClient
from MergeRequest import MergeRequest
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.port = port
        self.MAX_CLIENT = 5
        self.mergeDB = MergeRequest()
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
                logging.info(f"{addr} has connected")
                client.sendall(createMessage("info","hi", False))
                newClient = HandleClient(client, addr)
                threading.Thread(target = newClient.handleClient).start()
            except ConnectionResetError:
                print(f"Client{addr} Disconnected\n")
