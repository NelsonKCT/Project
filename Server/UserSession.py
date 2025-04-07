from UserInterFace import LoginUsers
from Message import decodeMessage, createMessage
from MergeRequest import MergeRequest
import sqlite3
import hashlib
import subprocess
import os
import json
import sys

class UserSession:
    def __init__(self, client, username):
        self.client = client
        self.username = username
        self.mergeDB = MergeRequest()

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
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}",False))
            ...
        username1, username2 ,user1_confirm, user2_confirm,user1_cid, user2_cid = data[1:]
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
        try :
            self.mergeDB.insertCID(self.username,requestID, CID)
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
            
            # Add Client directory to Python path if it's not already there
            if client_dir not in sys.path:
                sys.path.append(os.path.dirname(server_dir))
            
            # Import the upload_to_ipfs module and call its main function
            from Client.upload_to_ipfs import upload_encrypted_data_to_ipfs
            
            # Change working directory to Client directory temporarily
            original_dir = os.getcwd()
            os.chdir(client_dir)
            
            try:
                # Run the upload function and get CID directly
                cid = upload_encrypted_data_to_ipfs()
                
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
    
    def __del__(self):
        pass