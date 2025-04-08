import threading
import MergeRequest
import socket
class LoginUsers:
    _path = "./onlineUser.xlsx"
    _OnlineLoginUsers = {}
    _lock = threading.Lock()
    


    @staticmethod
    def getInitUI():
        strs = [
        "Options:\n",
        " 1. Check Online user\n",
        " 2. Send Merge Request\n"
        " 3. Check Merge Request\n",
        " 4. Confirm Merge Request\n",
        " 5. Start Merge Request\n",
        " 6. Send CID\n",
        " 7. Upload to IPFS\n",
        " 8. Get Partner CID\n",
        " 9. Download from IPFS"]
        return "".join(strs)
    @staticmethod   
    def update_Online_LoginUsers(username:str,client:socket,isLogin:bool):
        with LoginUsers._lock:
            if isLogin:
                LoginUsers._OnlineLoginUsers[username] = client
            else:
                LoginUsers._OnlineLoginUsers.pop(username)

        