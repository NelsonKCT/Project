import sqlite3
import shutil
import os
from datetime import datetime

def backup_database(db_path, backup_dir="backups"):
    """
    Create a backup of the database before making changes.
    """
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"mergeRequest_backup_{timestamp}.db")
        shutil.copyfile(db_path, backup_path)
        print(f"Backup created at: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Failed to create backup: {e}")
        raise

def get_existing_columns(cursor, table_name):
    """
    Retrieve the list of existing columns in the table.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def ensure_required_columns(db_path):
    """
    Verify and ensure the MERGE_REQUESTS table has all required CID columns for PSI steps.
    """
    # Define required columns for PSI steps 1, 2, and 3
    required_columns = [
        ("USER1_CID_STEP1", "TEXT", '""'),
        ("USER2_CID_STEP1", "TEXT", '""'),
        ("USER1_CID_STEP2", "TEXT", '""'),
        ("USER2_CID_STEP2", "TEXT", '""'),
        ("USER1_CID_STEP3", "TEXT", '""'),
        ("USER2_CID_STEP3", "TEXT", '""')
    ]
    
    # Backup the database
    backup_path = backup_database(db_path)
    
    # Connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if MERGE_REQUESTS table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='MERGE_REQUESTS'")
        if not cursor.fetchone():
            print("Error: MERGE_REQUESTS table does not exist in the database.")
            conn.close()
            return False
        
        # Get existing columns
        existing_columns = get_existing_columns(cursor, "MERGE_REQUESTS")
        print("\nCurrent columns in MERGE_REQUESTS:")
        for col in existing_columns:
            print(f"- {col}")
        
        # Add missing columns
        missing_columns = []
        for column_name, column_type, default_value in required_columns:
            if column_name not in existing_columns:
                missing_columns.append((column_name, column_type, default_value))
            else:
                print(f"Column {column_name} already exists.")
        
        if not missing_columns:
            print("\nAll required columns are present. No changes needed.")
        else:
            print("\nAdding missing columns:")
            for column_name, column_type, default_value in missing_columns:
                try:
                    cursor.execute(f"""
                        ALTER TABLE MERGE_REQUESTS
                        ADD COLUMN {column_name} {column_type} DEFAULT {default_value}
                    """)
                    print(f"Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"Error adding column {column_name}: {e}")
                    conn.close()
                    raise
            
            # Commit changes
            conn.commit()
            
            # Verify updated schema
            updated_columns = get_existing_columns(cursor, "MERGE_REQUESTS")
            print("\nUpdated columns in MERGE_REQUESTS:")
            for col in updated_columns:
                print(f"- {col}")
            
            # Confirm all required columns are now present
            missing = [col[0] for col in required_columns if col[0] not in updated_columns]
            if missing:
                print(f"\nError: The following required columns are still missing: {missing}")
                conn.close()
                return False
            else:
                print("\nAll required columns are now present.")
        
        conn.close()
        print("\nSchema verification and update completed successfully.")
        return True
    
    except Exception as e:
        print(f"Error during schema verification/update: {e}")
        if 'conn' in locals():
            conn.close()
        raise

if __name__ == "__main__":
    db_path = "/Users/nelsonkct/Documents/Project/Server/MergeRequestDataBase/mergeRequest.db"
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}. Please ensure the database exists.")
    else:
        try:
            success = ensure_required_columns(db_path)
            if success:
                print("Database is ready for use with PSI steps 1, 2, and 3.")
            else:
                print("Failed to ensure all required columns. Please check the error messages above.")
        except Exception as e:
            print(f"Error: {e}")