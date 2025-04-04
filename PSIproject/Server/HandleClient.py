from Message import createMessage, decodeMessage
from DataBase import DataBase
from hashlib import sha256
from UserInterFace import LoginUsers
from UserSession import UserSession
class HandleClient:
    def __init__(self, client, addr):
        self.client = client
        self.addr = addr
        self.dataBase = DataBase()
        self.isLogin = False
        self.username = None
    def handleClient(self):
        try:
            self.client.sendall(createMessage("info", "Welcome", False))
            while True:
                self.client.sendall(createMessage("info", "Enter R to Register L to login Q to quit",True))
                Letter = decodeMessage(self.client.recv(1024))
                if Letter["data"] == 'L':
                    if self.Login(): 
                        mainSession = UserSession(self.client,self.username)
                        mainSession.run()
                        del mainSession
                elif Letter["data"] == 'R':
                   self.Register()
                elif Letter["data"] == 'Q':
                    self.client.sendall(createMessage("info","Disconnecting...",False))
                    self.client.close()
                    break
                else:
                    self.client.sendall(createMessage("info", "invalid Input", False))
                    continue
        except ConnectionResetError:
            print(f"Client{self.addr} Disconnected")
    def Login(self):
        self.client.sendall(createMessage("info","Username:",True))
        username = decodeMessage(self.client.recv(1024))["data"]
        self.client.sendall(createMessage("info", "Password:", True))
        password = decodeMessage(self.client.recv(1024))["data"]
        if not self.dataBase.searchUserPassword(username,password)[0]:
            self.client.sendall(createMessage("info", "Wrong Username or Password",False))
            return False
        else:
            self.client.sendall(createMessage("info","Login Success", False))
            self.isLogin = True
            self.username = username
            LoginUsers.update_Online_LoginUsers(username,self.client,self.isLogin)
            return True


        ...
    def Register(self):
        while True:
            self.client.sendall(createMessage("info", "Username:", True))
            username = decodeMessage(self.client.recv(1024))["data"]
            if not self.dataBase.searchUser(username):
                break
            self.client.sendall(createMessage("info", "Username already Exists",False))
            
        password   = None 
        while True:
            self.client.sendall(createMessage("info", "PASSWORD:", True))
            password = decodeMessage(self.client.recv(1024))["data"]
            self.client.sendall(createMessage("info", "RE-ENTER PASSWORD:", True))
            if password == decodeMessage(self.client.recv(1024))["data"]:
                self.client.sendall(createMessage("info", "Register Success",False))
                try:
                    self.dataBase.addUser(username, password)
                except :
                    self.client.sendall("Username cant be blank")
                    break
                break
            self.client.sendall(createMessage("info","Password not the same",False))
