import socket
import threading
import sqlite3
import json
MAX_CLIENT  = 5
lock  = threading.Lock()
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
            client.sendall(json.dumps(createMessage("info","password does not match",True)).encode())
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
        conn.commit()
        conn.close()
        client.sendall(json.dumps(createMessage("info", "Login successfully", False)).encode())
        
    except sqlite3.IntegrityError:
        client.sendall(json.dumps(createMessage("info","Wrong username or password",False)).encode())
        return 1
    finally:
        lock.release()
    
    return 0
def createMessage(type, payload, reply_flag):
    message = {
        "type": type,
        "data": payload,
        "reply_required": reply_flag  
    }
    return message
def handleClient(client):
    while True:
        client.sendall(json.dumps(createMessage("info","ENTER R to Register L to Login",True)).encode())
        Letter = client.recv(1024).decode()
        p_Letter = json.loads(Letter)
        if p_Letter["data"] == "L":
           if Login(client) == 0:
            client.sendall(json.dumps(createMessage("info", "Login successfully", False)).encode())
            continue
        elif p_Letter["data"] == "R":
            if Register(client) == 0:
             client.sendall(json.dumps(createMessage("info", "Register successfully", False)).encode())
             continue
        else:
            client.sendall(json.dumps(createMessage("info", "invalid Input", False)).encode())
            continue
    return
def serverThread():
    # TCP connection
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    serverIP = '127.0.0.1'
    port = 8888
    #binding
    try:
        server.bind((serverIP,port))
    except:
        print("server init failed")
        return
    #listen
    server.listen(MAX_CLIENT)
    while True:
        client,addr = server.accept()
        print(f"Client{addr} Connected\n")
        client.sendall(json.dumps(createMessage("info", "hi",False)).encode())
        threading.Thread(target = handleClient,args = (client,)).start() 

    
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

