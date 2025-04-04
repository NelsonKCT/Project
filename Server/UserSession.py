from UserInterFace import LoginUsers
from Message import decodeMessage, createMessage
class UserSession:
    def __init__(self, client, username):
        self.client = client
        self.username = username

    def run(self):
        while True:
            self.client.sendall(createMessage("info", LoginUsers.getInitUI(), True))
            msg = decodeMessage(self.client.recv(1024))
            option = msg["data"]

            if option == '1': #Check Online User
                online = LoginUsers._OnlineLoginUsers
                self.client.sendall(createMessage("info", f"Online users: {', '.join(online)}", False))
            elif option == '2': #send Merge Request
                pass
            elif option == '3':#check merge Request
                pass
            elif option == '4':#confirm merge request
                pass
            elif option == '5':#start merge request
                pass
            elif option == 'Q':
                LoginUsers.update_Online_LoginUsers(self.username, False)
                self.client.sendall(createMessage("info", "Logging out...", False))
                break

            else:
                self.client.sendall(createMessage("info", "Invalid option", False))
    def __del__(self):
        pass