import sqlite3
import threading
class RequestDataBase:
    _lock = threading.Lock()
    def __init__(self):
        self.cursor = None
        self.conn = None
        self.path = "./RequestsDataBase/Request.db"
        self.init_dataBase()
    def init_dataBase(self):
        with RequestDataBase._lock:
            self.conn = sqlite3.connect(self.path)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS REQUESTS_CID(
                REQUEST_ID TEXT PRIMARY KEY NOT NULL,
                CID1 TEXT DEFAULT "",
                CID2 TEXT DEFAULT ""
                )
                """
            )
            self.conn.commit()
    def createRequest(self,requestID):
        with RequestDataBase._lock:
            try:
                    self.cursor.execute(
                        """
                        INSERT INTO REQUESTS_CID (REQUEST_ID)
                        VALUES(?)
                        """,(requestID,)
                    )
                    self.conn.commit()
            except sqlite3.IntegrityError:
                print("Request already Exists")
        
    def insertCID(self, CID,requestID):
        with RequestDataBase._lock:
            self.cursor.execute(
                """
                UPDATE REQUESTS_CID
                SET CID1 = ?
                WHERE REQUEST_ID = ?
                """,(CID, requestID)
            )
        ...