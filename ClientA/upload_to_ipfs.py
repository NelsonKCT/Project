import subprocess
import os
import json
import time

def upload_file_to_ipfs(file_path):
    """
    Upload a file to IPFS and return the CID
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        # Run IPFS add command
        result = subprocess.run(
            ["ipfs", "add", "-q", file_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"IPFS add command failed: {result.stderr}")
        
        # Extract CID from output
        cid = result.stdout.strip()
        return cid
    
    except Exception as e:
        raise RuntimeError(f"Failed to upload file to IPFS: {str(e)}")

def upload_encrypted_data_to_ipfs():
    """
    Upload encrypted data from the default location to IPFS
    """
    # Define the path to the encrypted data directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    encrypted_dir = os.path.join(current_dir, "encrypted_data")
    
    if not os.path.exists(encrypted_dir):
        os.makedirs(encrypted_dir, exist_ok=True)
        raise FileNotFoundError(f"Encrypted data directory not found: {encrypted_dir}")
    
    # Find the most recent file in the encrypted_data directory
    files = os.listdir(encrypted_dir)
    if not files:
        raise FileNotFoundError("No encrypted files found")
    
    # Sort files by modification time (newest first)
    encrypted_files = [os.path.join(encrypted_dir, f) for f in files 
                   if os.path.isfile(os.path.join(encrypted_dir, f)) and f.endswith(".enc")]
    
    if not encrypted_files:
        raise FileNotFoundError("No .enc encrypted files found")
    
    encrypted_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    latest_file = encrypted_files[0]
    
    # Upload the latest file to IPFS
    try:
        print(f"Uploading file: {latest_file}")
        cid = upload_file_to_ipfs(latest_file)
        
        # Save the CID to a file for reference
        cid_file = os.path.join(current_dir, "last_upload_cid.txt")
        with open(cid_file, "w") as f:
            f.write(cid)
        
        return cid
    
    except Exception as e:
        print(f"Error uploading encrypted data: {str(e)}")
        return None

if __name__ == "__main__":
    try:
        cid = upload_encrypted_data_to_ipfs()
        if cid:
            print(f"Successfully uploaded encrypted data. CID: {cid}")
        else:
            print("Failed to upload encrypted data.")
    except Exception as e:
        print(f"Error: {str(e)}") 