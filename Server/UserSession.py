from UserInterFace import LoginUsers
from Message import decodeMessage, createMessage
from MergeRequest import MergeRequest
import sqlite3
import hashlib
import subprocess
import os
import json
import sys
import importlib.util

class UserSession:
    def __init__(self, client, username):
        self.client = client
        self.username = username
        self.mergeDB = MergeRequest()
        
        # Initialize the local database manager
        client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Client")
        db_path = os.path.join(client_dir, "id_record.db")
        
        # Import the LocalDBManager class dynamically
        db_module_path = os.path.join(client_dir, "id_database.py")
        spec = importlib.util.spec_from_file_location("id_database", db_module_path)
        db_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(db_module)
        
        # Create an instance of LocalDBManager
        self.local_db = db_module.LocalDBManager(db_path)

    def run(self):
        while True:
            self.client.sendall(createMessage("info", LoginUsers.getInitUI(), True))
            msg = decodeMessage(self.client.recv(1024))
            option = msg["data"]

            if option == '1': #Check Online User
                online = LoginUsers._OnlineLoginUsers
                userList = "\n".join(online.keys())
                self.client.sendall(createMessage("info", userList, False))
            elif option == '2': #send Merge Request
                self.option2()
                pass
            elif option == '3':#check merge Request
                self.option3()
                pass
            elif option == '4':#confirm merge request
                self.option4()
                pass
            elif option == '5':#start merge request
                self.option5()
                pass
            elif option == '6':
                self.option6()
                pass
            elif option == '7':#upload to IPFS
                self.option7()
                pass
            elif option == '8':#get partner CID
                self.option8()
                pass
            elif option == '9':#download from IPFS
                self.option9()
                pass
            elif option == 'Q':
                LoginUsers.update_Online_LoginUsers(self.username,self.client ,False)
                self.client.sendall(createMessage("info", "Logging out...", False))
                break
            else:
                self.client.sendall(createMessage("info", "Invalid option", False))
    def option2(self):
        self.client.sendall(createMessage("info","Merge Partner:",True))
        username2 = decodeMessage(self.client.recv(1024))["data"]
        usernames = sorted([self.username, username2])
        combined = f"{usernames[0]}_{usernames[1]}".encode()
        requestID = hashlib.sha256()
        requestID.update(combined)

        try:
            self.mergeDB.createMergeRequest(RequestID=requestID.hexdigest(),username1=usernames[0], username2 =usernames[1])
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}",False))
        except sqlite3.IntegrityError as ie:
            self.client.sendall(createMessage("info", f"{ie}",False))
    def option3(self):
        try:
            result = "\n".join(self.mergeDB.checkAllMergeRequest(self.username))
            self.client.sendall(createMessage("info", result, False))
        except Exception as e:
            print(f"{e}")
        
        ...
    def option4(self):
        self.client.sendall(createMessage("info", "RequestsID:",True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            self.mergeDB.confirmMergeRequest(requestID,self.username)
            self.client.sendall(createMessage("info", "Confirm success", False))
        except Exception as e:
            print(f"{e}")
        ...
    def option5(self):
        """
            if requestID Exists
            if both users confirmed the request
            if both users are online
            send signal 
            both users start encrypt threading process
        """
        self.client.sendall(createMessage("info","RequestsID",True))

        
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            data = self.mergeDB.getRequest(requestID)
            username1, username2 ,user1_confirm, user2_confirm = data[1:5]
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}",False))
            ...
        if not (user1_confirm and user2_confirm):
            self.client.sendall(createMessage("info","request hasn't been confirmed by both parties", False))
            return
        bothUserOnline = (username1 in LoginUsers._OnlineLoginUsers) and (username2 in LoginUsers._OnlineLoginUsers)
        if not bothUserOnline:
            self.client.sendall(createMessage("info","Both user must be online", False))
            return
        client1 = LoginUsers._OnlineLoginUsers[username1]
        client2 = LoginUsers._OnlineLoginUsers[username2]
        client1.sendall(createMessage("signal",f"{requestID}", False))
        client2.sendall(createMessage("signal",f"{requestID}", False))
    def option6(self):
        self.client.sendall(createMessage("info","RequestsID",True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        self.client.sendall(createMessage("info" , "CID" , True))
        CID = decodeMessage(self.client.recv(1024))["data"]
        
        try:
            # Send CID to server
            self.mergeDB.insertCID(self.username, requestID, CID)
            
            # Also store in local database
            self.local_db.record_my_cid(requestID, CID)
            
            self.client.sendall(createMessage("info", "CID recorded successfully on server and local database", False))
        except ValueError as E:
            self.client.sendall(createMessage("info", f"{E}", False))

        ...
        
    def option7(self):
        """
        Execute the upload_to_ipfs.py script in the Client directory and return the CID to the user
        """
        self.client.sendall(createMessage("info", "Uploading Encrypted_Data to IPFS...", False))
        
        try:
            # Get the absolute path to the Client directory
            # Assuming the Client directory is at the same level as the Server directory
            server_dir = os.path.dirname(os.path.abspath(__file__))
            client_dir = os.path.join(os.path.dirname(server_dir), "Client")
            
            # Import the upload_to_ipfs module dynamically
            upload_module_path = os.path.join(client_dir, "upload_to_ipfs.py")
            spec = importlib.util.spec_from_file_location("upload_to_ipfs", upload_module_path)
            upload_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(upload_module)
            
            # Change working directory to Client directory temporarily
            original_dir = os.getcwd()
            os.chdir(client_dir)
            
            try:
                # Run the upload function and get CID directly
                cid = upload_module.upload_encrypted_data_to_ipfs()
                
                # Change back to the original directory
                os.chdir(original_dir)
                
                if cid:
                    status_msg = f"Upload successful!\nCID: {cid}\n"
                    self.client.sendall(createMessage("info", status_msg, False))
                else:
                    self.client.sendall(createMessage("info", "Upload failed to return a valid CID.", False))
            finally:
                # Ensure we go back to the original directory even if there's an error
                if os.getcwd() != original_dir:
                    os.chdir(original_dir)
                
        except Exception as e:
            error_msg = f"Failed to upload to IPFS: {str(e)}"
            self.client.sendall(createMessage("info", error_msg, False))
    
    def option8(self):
        """
        Get the partner's CID from the server and store it in the local database
        """
        self.client.sendall(createMessage("info", "Enter RequestID to get partner's CID:", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        
        try:
            # Get the merge request data from the server
            data = self.mergeDB.getRequest(requestID)
            
            # Extract user IDs and CIDs
            request_id, user1_id, user2_id, _, _, user1_cid, user2_cid = data
            
            # Determine which user is the partner and get their CID
            if self.username == user1_id:
                partner_username = user2_id
                partner_cid = user2_cid
            elif self.username == user2_id:
                partner_username = user1_id
                partner_cid = user1_cid
            else:
                self.client.sendall(createMessage("info", "You are not part of this merge request", False))
                return
            
            if not partner_cid:
                self.client.sendall(createMessage("info", f"Partner {partner_username} has not uploaded a CID yet", False))
                return
            
            # Store the partner's CID in the local database
            self.local_db.record_partner_cid(requestID, partner_cid)
            
            # Display CID info to the user
            response = f"Partner {partner_username}'s CID: {partner_cid}\n"
            response += "This CID has been saved to your local database.\n"
            response += "To retrieve their files: ipfs get " + partner_cid
            
            self.client.sendall(createMessage("info", response, False))
            
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error: {e}", False))
        except Exception as e:
            self.client.sendall(createMessage("info", f"Unexpected error: {e}", False))
    
    def option9(self):
        """
        Download files from IPFS using a CID
        """
        self.client.sendall(createMessage("info", "Enter the CID to download from IPFS:", True))
        cid = decodeMessage(self.client.recv(1024))["data"]
        
        if not cid:
            self.client.sendall(createMessage("info", "Error: No CID provided", False))
            return
        
        # Ask for download location
        self.client.sendall(createMessage("info", "Enter download location (leave blank for default 'Downloaded_Data'):", True))
        download_path = decodeMessage(self.client.recv(1024))["data"]
        
        if not download_path:
            # Get the Client directory path
            server_dir = os.path.dirname(os.path.abspath(__file__))
            client_dir = os.path.join(os.path.dirname(server_dir), "Client")
            download_path = os.path.join(client_dir, "Downloaded_Data")
        
        # Create the download directory if it doesn't exist
        os.makedirs(download_path, exist_ok=True)
        
        try:
            self.client.sendall(createMessage("info", f"Downloading from IPFS (CID: {cid})...", False))
            
            # Use subprocess to call the IPFS get command
            result = subprocess.run(
                ["ipfs", "get", "-o", download_path, cid],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Determine the downloaded file/folder path
                downloaded_path = os.path.join(download_path, os.path.basename(cid))
                
                # Prepare the success message
                success_msg = f"Successfully downloaded IPFS content with CID: {cid}\n"
                success_msg += f"Location: {downloaded_path}\n\n"
                
                self.client.sendall(createMessage("info", success_msg, False))
            else:
                error_msg = f"Error downloading from IPFS: {result.stderr}"
                self.client.sendall(createMessage("info", error_msg, False))
                
        except Exception as e:
            error_msg = f"Failed to download from IPFS: {str(e)}"
            self.client.sendall(createMessage("info", error_msg, False))
    
    def __del__(self):
        # Close the local database connection when the session ends
        if hasattr(self, 'local_db'):
            self.local_db.close()