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

def upload_to_ipfs(file_path):
    """
    Upload a file to IPFS and return its CID
    
    Args:
        file_path (str): Path to the file to upload
        
    Returns:
        str: CID of the uploaded file or None if upload failed
    """
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return None
    
    try:
        # Direct HTTP API call to the local IPFS daemon
        url = 'http://127.0.0.1:5001/api/v0/add'
        
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(url, files=files)
            
            if response.status_code == 200:
                result = response.json()
                cid = result['Hash']
                print(f"File uploaded to IPFS with CID: {cid}")
                return cid
            else:
                print(f"Error uploading to IPFS: HTTP {response.status_code}")
                print(response.text)
                return None
    
    except Exception as e:
        print(f"Error uploading to IPFS: {e}")
        return None

def send_cid_to_server(cid, server_address=("127.0.0.1", 8888)):
    """
    Send the CID of an uploaded file to the server
    
    Args:
        cid (str): The CID to send
        server_address (tuple): Tuple of (host, port) for the server
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not cid:
        print("Error: No CID provided")
        return False
    
    try:
        # Create socket connection to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(server_address)
        
        # Create message payload
        message = {
            "type": "file_upload",
            "data": cid,
            "reply_required": False
        }
        
        # Send the CID
        client.send(json.dumps(message).encode())
        print(f"CID sent to server successfully: {cid}")
        
        # Check for response (optional)
        try:
            client.settimeout(5)
            response = client.recv(1024).decode()
            if response:
                parsed_response = json.loads(response)
                print(f"Server response: {parsed_response['data']}")
        except socket.timeout:
            pass
        
        client.close()
        return True
        
    except Exception as e:
        print(f"Error sending CID to server: {e}")
        return False

def main():
    """Main function to handle file upload to IPFS"""
    print("IPFS Upload Tool")
    print("===============")
    
    # Check IPFS setup
    if not create_ipfs_network():
        print("Failed to set up IPFS network. Exiting.")
        return
    
    # Get file path
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Please enter the path to the file you want to upload to IPFS: ")
    
    # Ensure file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return
    
    # Upload to IPFS and get CID
    cid = upload_to_ipfs(file_path)
    if not cid:
        print("IPFS upload failed. Exiting.")
        return
    
    # Ask if the user wants to send the CID to the server
    send_to_server = input("Do you want to send the CID to the server? (y/n): ").lower()
    
    if send_to_server == 'y':
        # Get server address (optional)
        server_host = input("Enter server host (default: 127.0.0.1): ")
        if not server_host:
            server_host = "127.0.0.1"
        
        server_port = input("Enter server port (default: 8888): ")
        if not server_port:
            server_port = 8888
        else:
            server_port = int(server_port)
        
        # Send CID to server
        if send_cid_to_server(cid, (server_host, server_port)):
            print("CID sent to server successfully")
        else:
            print("Failed to send CID to server")
    
    print("\nSummary:")
    print(f"1. File: {file_path}")
    print(f"2. IPFS CID: {cid}")
    print(f"3. To retrieve file: ipfs cat {cid}")

if __name__ == "__main__":
    main() 