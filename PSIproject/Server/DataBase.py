import sqlite3
import threading
class DataBase: 
    _lock = threading.Lock()
    def __init__(self):
        self.path = 'UserDataBase/users.db'
        self.conn = None
        self.cursor = None
        self.init_database()
    def init_database(self):
        self.conn = sqlite3.connect(self.path,check_same_thread=False)
        self.cursor = self.conn.cursor()
        with DataBase._lock:
            self.cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS USER(
                    USERNAME TEXT PRIMARY KEY NOT NULL,
                    PASSWD TEXT NOT NULL
                    )
                """
            )
            self.conn.commit()    
        return
    @property
    def get_cursor(self):
        if self.cursor == None:
            raise NotImplementedError("Please init DataBase First")
        return self.cursor
    def addUser(self,username, password):
        with DataBase._lock:
            self.cursor.execute(
                """
                    INSERT INTO USER (USERNAME, PASSWD)
                    VALUES(?, ?)
                """,(username,password)
            )
            self.conn.commit()
        return
            
    def searchUser(self,username):
        user = None
        with DataBase._lock:
            self.cursor.execute(
                """
                    SELECT * FROM USER WHERE USERNAME == ?
                """,(username,)
            )
            user = self.cursor.fetchall()
        if not user :
            return False 
        else:
            return True 
    def searchUserPassword(self,username, password):
        user  = None
        with DataBase._lock:
            self.cursor.execute(
                """
                    SELECT * FROM USER WHERE USERNAME == ? AND PASSWD == ?
                """,(username,password)
            )
        user = self.cursor.fetchall()
        if not user :
            return (False, "")
        else:
            return (True,user[0])
        
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None