import socket
import threading
import sympy
import sqlite3
import json

MAX_CLIENT  = 5
lock  = threading.Lock()
UserClientDict = {}
def createMessage(type, payload, reply_flag):
    message = {
        "type": type,
        "data": payload,
        "reply_required": reply_flag  
    }
    return message
def init_database():
    conn = sqlite3.connect('DataBase/users.db')
    cursor = conn.cursor()
    lock.acquire()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS USER(
            USERNAME TEXT PRIMARY KEY NOT NULL, 
            PASSWD   TEXT  NOT NULL 
            )
        """
    )
    lock.release()
    conn.commit()
    conn.close()
    return 0
def Register(client):
    client.sendall(json.dumps(createMessage("request","Please enter your username",True)).encode())
    username =client.recv(1024).decode()
    p_username = json.loads(username)
    print(p_username["data"])
    
    while True:
        client.sendall(json.dumps(createMessage("request","Please enter your password",True)).encode())
        passwd = client.recv(1024).decode()

        p_passwd = json.loads(passwd)

        client.sendall(json.dumps(createMessage("request","Please reenter your password",True)).encode())

        passwd1 = client.recv(1024).decode()

        p_passwd1 = json.loads(passwd1)

        if p_passwd["data"]!=p_passwd1["data"]:
            client.sendall(json.dumps(createMessage("info","password does not match",False)).encode())
            continue
        else:
            break
    try:
        conn = sqlite3.connect("DataBase/users.db")
        cursor  = conn.cursor()
        lock.acquire()
        cursor.execute(
            """
                INSERT INTO USER (USERNAME,PASSWD)
                VALUES(?, ?)
            """,(p_username["data"], p_passwd["data"])
        )
        conn.commit()   
        conn.close()
    except sqlite3.IntegrityError:
        client.sendall(json.dumps(createMessage("info","User name already exists",False)).encode())
        return
    finally:
        lock.release()
    client.sendall(json.dumps(createMessage("info", "Account create successfully",False)).encode())
    return
def Login(client):
    client.sendall(json.dumps(createMessage("request","Please enter your username",True)).encode())
    username =client.recv(1024).decode()
    p_username = json.loads(username)  
    client.sendall(json.dumps(createMessage("request","Please enter your password",True)).encode())
    passwd = client.recv(1024).decode()

    p_passwd = json.loads(passwd)
    try:
        conn = sqlite3.connect('DataBase/users.db')
        cursor = conn.cursor()
        lock.acquire()
        cursor.execute(
            """
                SELECT * FROM USER WHERE USERNAME == ? AND PASSWD == ?
            """,(p_username["data"], p_passwd["data"])
        )
        user_data = cursor.fetchall()
        conn.close()
        
        
    except sqlite3.IntegrityError:
        client.sendall(json.dumps(createMessage("info",f"DataBase error{str(sqlite3.IntegrityError)}",False)).encode())
        return 1 , None
    finally:
        lock.release()
    if not user_data:
        client.sendall(json.dumps(createMessage("info","Wrong username or password",False)).encode())
        return 1, None
    else:
        client.sendall(json.dumps(createMessage("info", "Login successfully", False)).encode())
        UserClientDict[p_username["data"]] = client
        return 0 , p_username["data"]

def handleClient(client,addr):
    try:
        while True:
            client.sendall(json.dumps(createMessage("info","ENTER R to Register L to Login",True)).encode())
            Letter = client.recv(1024).decode()
            p_Letter = json.loads(Letter)
            if p_Letter["data"] == "L":
                value , name = Login(client)
                if value == 0:
                    afterLogin(client,name)
                    break
            elif p_Letter["data"] == "R":
                if Register(client) == 0:
                    client.sendall(json.dumps(createMessage("info", "Register successfully", False)).encode())
                    continue
            else:
                client.sendall(json.dumps(createMessage("info", "invalid Input", False)).encode())
                continue
    except ConnectionResetError:
        print(f"Client{addr} Disconnected")
    return
def afterLogin(client, username):
    while True:
        client.sendall(json.dumps(createMessage("info", f"Welcome {username}", False)).encode())
        client.sendall(json.dumps(createMessage("info", "Perform operation:\n1.Send Merge Request\n2.Check Merge Request\n")))
        for key ,val in UserClientDict.items():
            client.sendall(json.dumps(createMessage("info", f"{key}",False)).encode())
        client.sendall(json.dumps(createMessage ("info", f"Please Choose user data to merge", True)).encode())
        r_username = client.recv(1024).decode()
        p_r_username = json.loads(r_username)
        client.sendall(json.dumps(createMessage ("info", f"sending request to {p_r_username['data']}", False)).encode())
        UserClientDict[p_r_username['data']].sendall(json.dumps(createMessage("info", f"merge request from {username}",False)).encode())
        break
    return
def serverThread():
    # TCP connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    serverIP = '127.0.0.1'
    port = 8888
    #binding
    try:
        server.bind((serverIP,port))
    except :
        print("server init failed")
        return
    #listen
    server.listen(MAX_CLIENT)
    while True:
        try:
            client,addr = server.accept()
            print(f"Client{addr} Connected\n")
            client.sendall(json.dumps(createMessage("info", "hi",False)).encode())
            threading.Thread(target = handleClient,args = (client,addr,)).start()
        except ConnectionResetError:
            print(f"Client{addr} Disconnected\n")

def generatePrime():
    prime = sympy.randprime(2**511,2**512)
    return prime
def main():
    ServerDown = False
    print("Server Starting ... ")
    init_database()
    #server background Thread
    threading.Thread(target = serverThread,daemon = True).start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server shutting down")
        return
if __name__ == "__main__":
    main()

