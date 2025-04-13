import os
import sys
import time
import json
import socket
import requests
import subprocess

def create_ipfs_network():
    """
    Check if IPFS is installed and running, start it if needed
    
    Returns:
        success: Boolean indicating if IPFS is running
    """
    try:
        # Check if IPFS is running
        result = subprocess.run(['ipfs', 'swarm', 'peers'], capture_output=True, text=True) 
        if result.returncode == 0:
            print("IPFS daemon is already running")
            return True
        
        print("IPFS daemon is not running, attempting to start...")
        try:
            # Start IPFS daemon in background
            os.system('ipfs daemon &')
            print("IPFS daemon started")
            # Give daemon time to start
            time.sleep(3)
            return True
        except Exception as e:
            print(f"Failed to start IPFS daemon: {e}")
            print("Please install IPFS and start the daemon manually:")
            print("1. Install IPFS from https://docs.ipfs.io/install/")
            print("2. Initialize IPFS with 'ipfs init'")
            print("3. Start the daemon with 'ipfs daemon'")
            return False
    except Exception as e:
        print(f"Error checking IPFS status: {e}")
        return False


def upload_directory_to_ipfs(directory_path):
    """
    Upload an entire directory to IPFS and return its CID
    
    Args:
        directory_path (str): Path to the directory to upload
        
    Returns:
        str: CID of the uploaded directory or None if upload failed
    """
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found")
        return None
    
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a directory")
        return None
    
    try:
        # Use subprocess to call IPFS directly for directory upload
        result = subprocess.run(
            ['ipfs', 'add', '-r', '-Q', directory_path], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            cid = result.stdout.strip()
            print(f"Directory uploaded to IPFS with CID: {cid}")
            return cid
        else:
            print(f"Error uploading directory to IPFS: {result.stderr}")
            return None
    
    except Exception as e:
        print(f"Error uploading directory to IPFS: {e}")
        return None

def upload_encrypted_data_to_ipfs():
    """
    Upload the Encrypted_Data directory to IPFS and return the CID
    
    Returns:
        str: CID of the uploaded directory or None if upload failed
    """
    print("IPFS Upload Tool")
    print("===============")
    
    # Check IPFS setup
    if not create_ipfs_network():
        print("Failed to set up IPFS network. Exiting.")
        return None
    
    # Default to uploading the Encrypted_Data directory
    encrypted_data_dir = "Encrypted_Data"
    
    # Check if directory exists
    if not os.path.exists(encrypted_data_dir):
        print(f"Error: '{encrypted_data_dir}' directory not found.")
        print("Please run the encryption process first.")
        return None
    
    # Upload directory to IPFS
    print(f"Uploading the entire '{encrypted_data_dir}' folder to IPFS...")
    cid = upload_directory_to_ipfs(encrypted_data_dir)
    
    if not cid:
        print("IPFS upload failed. Exiting.")
        return None
        
    return cid

# For backward compatibility, keep main() but make it call the new function
def main():
    return upload_encrypted_data_to_ipfs()

if __name__ == "__main__":
    main() 