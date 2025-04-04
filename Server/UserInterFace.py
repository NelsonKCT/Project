import threading
import MergeRequest
class LoginUsers:
    _path = "./onlineUser.xlsx"
    _OnlineLoginUsers = set()
    _lock = threading.Lock()


    @staticmethod
    def getInitUI():
        strs = [
        "Options:\n",
        " 1. Check Online user\n",
        " 2. Send Merge Request\n"
        " 3. Check Merge Request\n",
        " 4. Confirm Merge Request\n",
        " 5. Start Merge Request"]
        return "".join(strs)
    @staticmethod   
    def update_Online_LoginUsers(username:str,isLogin:bool):
        with LoginUsers._lock:
            if isLogin:
                LoginUsers._OnlineLoginUsers.add(username)
            else:
                LoginUsers._OnlineLoginUsers.discard(username) 

        