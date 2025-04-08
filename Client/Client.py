import socket
import json
import os
import importlib.util
import subprocess

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", 8888))
        print("Connected to the server.")
    except ConnectionRefusedError:
        print("Connection failed. Is the server running?")
        return
    
    try:
        while True:
            # Receiving data from the server
            data = client.recv(1024).decode()
            if not data:
                print("Server closed the connection.")
                break
            parsed_data = json.loads(data)
            print(parsed_data['data'])
            
            if parsed_data['reply_required'] == True:
                # Sending data to the server
                payload = input()
                message = createMessage("response", payload, False)
                if payload.lower() == "exit":
                    print("Closing connection.")
                    break
                client.send(json.dumps(message).encode())
            elif parsed_data['type'] == "prime":
                with open("prime.txt", "w") as file:
                    file.write(str(parsed_data['data']))
            elif parsed_data['type'] == "signal":
                if parsed_data['data'].startswith("upload_to_ipfs"):
                    print("Uploading to IPFS...")
                    try:
                        # Import the upload_to_ipfs module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        upload_module_path = os.path.join(current_dir, "upload_to_ipfs.py")
                        spec = importlib.util.spec_from_file_location("upload_to_ipfs", upload_module_path)
                        upload_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(upload_module)
                        
                        # Execute the upload function
                        cid = upload_module.upload_encrypted_data_to_ipfs()
                        
                        if cid:
                            # Send the CID back to the server
                            response = createMessage("info", f"Upload successful! CID: {cid}", False)
                            client.send(json.dumps(response).encode())
                        else:
                            response = createMessage("info", "Upload failed to return a valid CID", False)
                            client.send(json.dumps(response).encode())
                    except Exception as e:
                        error_msg = f"Failed to upload to IPFS: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("download_from_ipfs:"):
                    try:
                        # Extract download info from the signal
                        download_info = json.loads(parsed_data['data'].split(":", 1)[1])
                        cid = download_info['cid']
                        download_path = download_info['download_path']
                        
                        # Create download directory if it doesn't exist
                        os.makedirs(download_path, exist_ok=True)
                        
                        print(f"Downloading from IPFS (CID: {cid})...")
                        
                        # Execute IPFS get command
                        result = subprocess.run(
                            ["ipfs", "get", "-o", download_path, cid],
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0:
                            # Determine the downloaded file/folder path
                            downloaded_path = os.path.join(download_path, os.path.basename(cid))
                            success_msg = f"Successfully downloaded IPFS content with CID: {cid}\n"
                            success_msg += f"Location: {downloaded_path}\n\n"
                            response = createMessage("info", success_msg, False)
                        else:
                            error_msg = f"Error downloading from IPFS: {result.stderr}"
                            response = createMessage("info", error_msg, False)
                        
                        client.send(json.dumps(response).encode())
                    except Exception as e:
                        error_msg = f"Failed to download from IPFS: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                else:
                    print(f"Received signal: {parsed_data['data']}")
            else:
                continue
    except KeyboardInterrupt:
        print("\nConnection interrupted by user.")
    finally:
        client.close()

def createMessage(type, payload, reply_flag):
    message = {
        "type": type,
        "data": payload,
        "reply_required": reply_flag  
    }
    return message

if __name__ == "__main__":
    main()