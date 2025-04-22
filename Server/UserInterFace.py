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
        "┌──────────────────────────────────────┐\n",
        "│      Secure Data Matching System     │\n",
        "└──────────────────────────────────────┘\n",
        "\n",
        "Available Actions:\n",
        "1. View Online Users\n",
        "2. Create Merge Request\n"
        "3. View Pending Requests\n",
        "4. Approve Merge Request\n",
        "5. Initialize Merge Operation\n",
        "6. Private Set Intersection Protocol\n",
        "\n",
        "Q. Logout\n",
        "\n",
        "Enter your selection: "
        ]
        return "".join(strs)
    @staticmethod   
    def update_Online_LoginUsers(username:str,client:socket,isLogin:bool):
        with LoginUsers._lock:
            if isLogin:
                LoginUsers._OnlineLoginUsers[username] = client
            else:
                LoginUsers._OnlineLoginUsers.pop(username)

        