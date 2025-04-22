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
            self.client.sendall(createMessage("info", "Welcome to Secure Data Matching Platform\n===================================", False))
            while True:
                self.client.sendall(createMessage("info", "Please select an option:\n[L] Login\n[R] Register\n[Q] Quit", True))
                Letter = decodeMessage(self.client.recv(1024))
                if Letter["data"].upper() == 'L':
                    if self.Login(): 
                        mainSession = UserSession(self.client, self.username)
                        mainSession.run()
                        del mainSession
                elif Letter["data"].upper() == 'R':
                   self.Register()
                elif Letter["data"].upper() == 'Q':
                    self.client.sendall(createMessage("info", "Thank you for using our service. Disconnecting...", False))
                    self.client.close()
                    break
                else:
                    self.client.sendall(createMessage("info", "Invalid selection. Please enter L, R, or Q.", False))
                    continue
        except ConnectionError:
            self.client.close()
            print(f"Client{self.addr} Disconnected")
    def Login(self):
        self.client.sendall(createMessage("info", "Username:", True))
        username = decodeMessage(self.client.recv(1024))["data"]
        self.client.sendall(createMessage("info", "Password:", True))
        password = decodeMessage(self.client.recv(1024))["data"]
        if not self.dataBase.searchUserPassword(username, password)[0]:
            self.client.sendall(createMessage("info", "Authentication failed: Invalid username or password", False))
            return False
        else:
            self.client.sendall(createMessage("info", "Authentication successful. Welcome, " + username + "!", False))
            self.isLogin = True
            self.username = username
            LoginUsers.update_Online_LoginUsers(username, self.client, self.isLogin)
            return True
    def Register(self):
        while True:
            self.client.sendall(createMessage("info", "Create Username:", True))
            username = decodeMessage(self.client.recv(1024))["data"]
            if not self.dataBase.searchUser(username):
                break
            self.client.sendall(createMessage("info", "This username is already taken. Please choose another one.", False))
            
        password = None 
        while True:
            self.client.sendall(createMessage("info", "Create Password:", True))
            password = decodeMessage(self.client.recv(1024))["data"]
            self.client.sendall(createMessage("info", "Confirm Password:", True))
            if password == decodeMessage(self.client.recv(1024))["data"]:
                self.client.sendall(createMessage("info", "Account created successfully! You can now login with your credentials.", False))
                try:
                    self.dataBase.addUser(username, password)
                except:
                    self.client.sendall("Error: Username cannot be blank.")
                    break
                break
            self.client.sendall(createMessage("info", "Passwords do not match. Please try again.", False))
