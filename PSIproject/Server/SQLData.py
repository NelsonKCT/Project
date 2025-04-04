import sqlite3

def print_all_values(db_path, table_name):
    try:
        conn = sqlite3.connect(db_path)  # Connect to the database
        cursor = conn.cursor()
        
        # Fetch all rows from the table
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Print column names
        column_names = [description[0] for description in cursor.description]
        print(" | ".join(column_names))
        print("-" * 50)

        # Print all rows
        for row in rows:
            print(" | ".join(map(str, row)))
    
    except sqlite3.Error as e:
        print(f"SQLite Error: {e}")
    
    finally:
        conn.close()  # Always close the connection

# Example Usage
print_all_values("UserDataBAse/users.db", "USER")
print_all_values("MergeRequestDataBAse/mergeRequest.db","MERGE_REQUESTS")