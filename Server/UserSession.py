
from UserInterFace import LoginUsers
from Message import decodeMessage, createMessage
from MergeRequest import MergeRequest
import sqlite3
import hashlib
class UserSession:
    def __init__(self, client, username):
        self.client = client
        self.username = username
        self.mergeDB = MergeRequest()

    def run(self):
        while True:
            self.client.sendall(createMessage("info", LoginUsers.getInitUI(), True))
            msg = decodeMessage(self.client.recv(1024))
            option = msg["data"]

            if option == '1': #Check Online User
                online = LoginUsers._OnlineLoginUsers
                userList = "\n".join(online.keys())
                self.client.sendall(createMessage("info", userList, False))
            elif option == '2': #send Merge Request
                self.option2()
                pass
            elif option == '3':#check merge Request
                self.option3()
                pass
            elif option == '4':#confirm merge request
                self.option4()
                pass
            elif option == '5':#start merge request
                self.option5()
                pass
            elif option == 'Q':
                LoginUsers.update_Online_LoginUsers(self.username,self.client ,False)
                self.client.sendall(createMessage("info", "Logging out...", False))
                break
            else:
                self.client.sendall(createMessage("info", "Invalid option", False))
    def option2(self):
        self.client.sendall(createMessage("info","Merge Partner:",True))
        username2 = decodeMessage(self.client.recv(1024))["data"]
        usernames = sorted([self.username, username2])
        combined = f"{usernames[0]}_{usernames[1]}".encode()
        requestID = hashlib.sha256()
        requestID.update(combined)

        try:
            self.mergeDB.createMergeRequest(RequestID=requestID.hexdigest(),username1=usernames[0], username2 =usernames[1])
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}",False))
        except sqlite3.IntegrityError as ie:
            self.client.sendall(createMessage("info", f"{ie}",False))
    def option3(self):
        try:
            result = "\n".join(self.mergeDB.checkAllMergeRequest(self.username))
            self.client.sendall(createMessage("info", result, False))
        except Exception as e:
            print(f"{e}")
        
        ...
    def option4(self):
        self.client.sendall(createMessage("info", "RequestsID:",True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            self.mergeDB.confirmMergeRequest(requestID,self.username)
            self.client.sendall(createMessage("info", "Confirm success", False))
        except Exception as e:
            print(f"{e}")
        ...
    def option5(self):
        self.client.sendall(createMessage("info","ReqeustsID",True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            ...
        except:
            ...
        
        ...
        
    def __del__(self):
        pass