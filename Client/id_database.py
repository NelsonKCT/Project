import sqlite3
import os
import threading

class LocalDBManager:
    _lock = threading.Lock()
    
    def __init__(self, db_path="id_record.db"):
        """
        Initialize the local database manager
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.init_database()
        
    def init_database(self):
        """Initialize the database and create tables if they don't exist"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        with LocalDBManager._lock:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS MERGE_RECORDS (
                    request_id TEXT PRIMARY KEY,
                    my_cid TEXT,
                    partner_cid TEXT
                )
                """
            )
            self.conn.commit()
        return
    
    def record_my_cid(self, request_id, my_cid):
        """
        Record or update the user's CID for a specific request
        
        Args:
            request_id (str): The merge request ID
            my_cid (str): User's CID for the encrypted data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with LocalDBManager._lock:
                # Check if record exists
                self.cursor.execute(
                    "SELECT * FROM MERGE_RECORDS WHERE request_id = ?",
                    (request_id,)
                )
                existing_record = self.cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    self.cursor.execute(
                        "UPDATE MERGE_RECORDS SET my_cid = ? WHERE request_id = ?",
                        (my_cid, request_id)
                    )
                else:
                    # Insert new record
                    self.cursor.execute(
                        "INSERT INTO MERGE_RECORDS (request_id, my_cid, partner_cid) VALUES (?, ?, NULL)",
                        (request_id, my_cid)
                    )
                
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error recording CID: {e}")
            return False
    
    def record_partner_cid(self, request_id, partner_cid):
        """
        Record or update a partner's CID for a specific request
        
        Args:
            request_id (str): The merge request ID
            partner_cid (str): Partner's CID for the encrypted data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with LocalDBManager._lock:
                # Check if record exists
                self.cursor.execute(
                    "SELECT * FROM MERGE_RECORDS WHERE request_id = ?",
                    (request_id,)
                )
                existing_record = self.cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    self.cursor.execute(
                        "UPDATE MERGE_RECORDS SET partner_cid = ? WHERE request_id = ?",
                        (partner_cid, request_id)
                    )
                else:
                    # Insert new record
                    self.cursor.execute(
                        "INSERT INTO MERGE_RECORDS (request_id, my_cid, partner_cid) VALUES (?, NULL, ?)",
                        (request_id, partner_cid)
                    )
                
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Error recording partner CID: {e}")
            return False
    
    def get_merge_record(self, request_id):
        """
        Get the merge record for a specific request
        
        Args:
            request_id (str): The merge request ID
            
        Returns:
            tuple: (my_cid, partner_cid) or (None, None) if not found
        """
        try:
            with LocalDBManager._lock:
                self.cursor.execute(
                    "SELECT my_cid, partner_cid FROM MERGE_RECORDS WHERE request_id = ?",
                    (request_id,)
                )
                record = self.cursor.fetchone()
                
                if record:
                    return record
                else:
                    return (None, None)
        except Exception as e:
            print(f"Error retrieving merge record: {e}")
            return (None, None)
    
    def get_all_merge_records(self):
        """
        Get all merge records
        
        Returns:
            list: List of tuples (request_id, my_cid, partner_cid)
        """
        try:
            with LocalDBManager._lock:
                self.cursor.execute("SELECT request_id, my_cid, partner_cid FROM MERGE_RECORDS")
                records = self.cursor.fetchall()
                return records
        except Exception as e:
            print(f"Error retrieving all merge records: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
