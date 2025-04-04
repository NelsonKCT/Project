import sqlite3
import threading
class MergeRequest:
    _lock = threading.Lock()
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.path = './MergeRequestDataBase/mergeRequest.db'
    def init_merge_database(self):
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
                CREATE TABLE IF NOT EXIST MERGE_REQUESTS(
                REQUESTS_ID TEXT PRIMARY KEY NOT NULL,
                USER1_ID TEXT NOT NULL,
                USER2_ID TEXT NOT NULL
                USER1_CONFIRM BOOLEAN DEFAULT FALSE,
                USER2_CONFIRM BOOLEAN DEFAULT FALSE     
               )
            """
        )
    @staticmethod
    def SendMergeRequest(username1, username2):
        
        ...
    @staticmethod
    def checkMergeRequest():
        ...
    @staticmethod 
    def confirmMergeRequest():
        ...