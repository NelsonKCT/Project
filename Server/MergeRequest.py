
import sqlite3
import threading
from DataBase import DataBase
class MergeRequest:
    _lock = threading.Lock()
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.path = './MergeRequestDataBase/mergeRequest.db'
        self.database = DataBase()
        self.init_merge_database()
        
    def init_merge_database(self):
        with MergeRequest._lock:
            self.conn = sqlite3.connect(self.path)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                """
                    CREATE TABLE IF NOT EXISTS MERGE_REQUESTS(
                    REQUESTS_ID TEXT PRIMARY KEY NOT NULL,
                    USER1_ID TEXT NOT NULL,
                    USER2_ID TEXT NOT NULL,
                    USER1_CONFIRM BOOLEAN DEFAULT FALSE,
                    USER2_CONFIRM BOOLEAN DEFAULT FALSE     
                )
                """
            )
            self.conn.commit()
    def createMergeRequest(self,username1, username2, RequestID):
        if not (self.database.searchUser(username1)and self.database.searchUser(username2)):
            raise ValueError("user does not exists")
        if username1 == username2:
            raise ValueError("username cant be the same")
        with MergeRequest._lock:
            try:
                self.cursor.execute(
                    """
                        INSERT INTO MERGE_REQUESTS (REQUESTS_ID, USER1_ID, USER2_ID)
                        VALUES(?,?,?)
                    """,(RequestID, username1,username2)
                ) 
                self.conn.commit()
            except sqlite3.IntegrityError:
                raise sqlite3.IntegrityError("Requests Exists")
        
    def isReady(self,requestID):
        with MergeRequest._lock:
            try:
                self.cursor.execute(
                    """
                        SELECT USER1_CONFIRM, USER2_CONFIRM 
                        FROM MERGE_REQUESTS
                        WHERE REQUESTID = ?
                    """,(requestID)
                )
                result  = self.cursor.fetchone()
                if not result :
                    raise ValueError("Request does not exist")
            except:
                ...
        ...
    def checkAllMergeRequest(self, username):
        with MergeRequest._lock:
            try:
                self.cursor.execute(
                    """
                        SELECT *
                        FROM MERGE_REQUESTS 
                        WHERE USER1_ID = ? OR USER2_ID = ? 
                    """,(username,username)
                )

                result  = self.cursor.fetchall()
                List_result = [row[0] for row in  result]
                if not result:
                    raise ValueError("You dont have a single request")
                return List_result
            except Exception as e:
                print(f"{e}")
                return None
                ...
        
        ...
    def confirmMergeRequest(self,requestID,username):
        with MergeRequest._lock:
            try:
                self.cursor.execute(
                    """
                    SELECT USER1_ID, USER2_ID FROM MERGE_REQUESTS WHERE REQUESTS_ID = ?
                    """,
                    (requestID,)
                )
                result = self.cursor.fetchone()  # get single row

                if not result:
                    raise ValueError("Request ID not found.")

                user1_id, user2_id = result

                if username == user1_id:
                    self.cursor.execute(
                        """
                        UPDATE MERGE_REQUESTS
                        SET USER1_CONFIRM = TRUE
                        WHERE REQUESTS_ID = ?
                        """,
                        (requestID,)
                    )
                    self.conn.commit()
                elif username == user2_id:
                    self.cursor.execute(
                        """
                        UPDATE MERGE_REQUESTS
                        SET USER2_CONFIRM = TRUE
                        WHERE REQUESTS_ID = ?
                        """,
                        (requestID,)
                    )
                    self.conn.commit()
                else:
                     raise ValueError("User is not part of this merge request.")

            except Exception as e:
                print(f"Error confirming merge request: {e}")
        ...