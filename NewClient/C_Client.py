import socket,threading
from Message import createMessage, decodeMessage
from collections import deque
from Request import RequestDataBase
import time

class Client:
    _lock = threading.Lock()
    def __init__(self, host:str , port:int):
        self.socket = None
        self.host  = host 
        self.port = port
        self.msg_buffer = deque()
        self.signal_buffer = deque()
        self.requestDB = RequestDataBase()
        self.requestDB.init_dataBase()
    def connect(self):
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try :
            self.socket.connect((self.host, self.port))
            print("Connected to the server.")
        except ConnectionRefusedError:
            print("Connection failed. Is the server running?")
            return
    def receive(self):
        while True:
            try :
                raw = self.socket.recv(1024)
                if raw: 
                    with Client._lock:
                        data = decodeMessage(raw)
                        if data["type"] == "signal":
                            self.signal_buffer.append(data)
                        else:
                            self.msg_buffer.append(data)
            except ConnectionError as e:
                print(f"Receive Failed: {e}")
                return
    def script(self):
        ...
    def signal_handling(self):
        while True:
            with Client._lock:
                if not self.signal_buffer:
                    break
                signal =  self.signal_buffer.popleft()
            self.requestDB.createRequest(signal["data"])
    def logic(self):
            try:
                with Client._lock:
                    msg = self.msg_buffer.popleft()
                print(msg["data"])
                if msg["reply_required"] == True:
                    self.socket.sendall(createMessage("response", input("Reply:"),False))

            except IndexError:
                pass
