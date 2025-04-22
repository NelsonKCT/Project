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
import random
import sympy

def generate_deterministic_prime(request_id):
    """
    Generate a deterministic prime number from a request ID.
    
    Args:
        request_id (str): The request ID to use as a seed
    
    Returns:
        int: A large prime number derived from the request ID
    """
    # Use the request_id as a seed for the random generator
    # This ensures that the same request_id always produces the same prime
    seed = int(hashlib.sha256(request_id.encode()).hexdigest(), 16)
    random.seed(seed)
    
    # Generate a random number in the range 2^511 to 2^512 - 1
    lower_bound = 2**511
    upper_bound = 2**512 - 1
    candidate = random.randint(lower_bound, upper_bound)
    
    # Find the next prime after the candidate
    prime = sympy.nextprime(candidate)
    
    # Reset the random seed to ensure it doesn't affect other operations
    random.seed()
    
    return prime

class UserSession:
    def __init__(self, client, username):
        self.client = client
        self.username = username
        self.mergeDB = MergeRequest()
        self.last_request_id = None  # Store the last used request ID
        self.last_psi_step = 1  # Start with step 1

    def run(self):
        while True:
            self.client.sendall(createMessage("info", LoginUsers.getInitUI(), True))
            msg = decodeMessage(self.client.recv(1024))
            option = msg["data"]

            if option == '1':
                online = LoginUsers._OnlineLoginUsers
                userList = "\n".join(online.keys())
                self.client.sendall(createMessage("info", userList, False))
            elif option == '2':
                self.option2()
            elif option == '3':
                self.option3()
            elif option == '4':
                self.option4()
            elif option == '5':
                self.option5()
            elif option == '6':
                self.psi_protocol()
            elif option == 'Q':
                LoginUsers.update_Online_LoginUsers(self.username, self.client, False)
                self.client.sendall(createMessage("info", "Logging out...", False))
                break
            else:
                self.client.sendall(createMessage("info", "Invalid option", False))

    def option2(self):
        self.client.sendall(createMessage("info", "Merge Partner:", True))
        username2 = decodeMessage(self.client.recv(1024))["data"]
        usernames = sorted([self.username, username2])
        combined = f"{usernames[0]}_{usernames[1]}".encode()
        requestID = hashlib.sha256()
        requestID.update(combined)

        try:
            self.mergeDB.createMergeRequest(RequestID=requestID.hexdigest(), username1=usernames[0], username2=usernames[1])
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}", False))
        except sqlite3.IntegrityError as ie:
            self.client.sendall(createMessage("info", f"{ie}", False))

    def option3(self):
        try:
            result = "\n".join(self.mergeDB.checkAllMergeRequest(self.username))
            self.client.sendall(createMessage("info", result, False))
        except Exception as e:
            print(f"{e}")

    def option4(self):
        self.client.sendall(createMessage("info", "RequestsID:", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            self.mergeDB.confirmMergeRequest(requestID, self.username)
            self.client.sendall(createMessage("info", "Confirm success", False))
        except Exception as e:
            print(f"{e}")

    def option5(self):
        self.client.sendall(createMessage("info", "RequestsID", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        try:
            data = self.mergeDB.getRequest(requestID)
            username1, username2, user1_confirm, user2_confirm = data[1:5]
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}", False))
            return
        if not (user1_confirm and user2_confirm):
            self.client.sendall(createMessage("info", "request hasn't been confirmed by both parties", False))
            return
        bothUserOnline = (username1 in LoginUsers._OnlineLoginUsers) and (username2 in LoginUsers._OnlineLoginUsers)
        if not bothUserOnline:
            self.client.sendall(createMessage("info", "Both user must be online", False))
            return
        client1 = LoginUsers._OnlineLoginUsers[username1]
        client2 = LoginUsers._OnlineLoginUsers[username2]
        client1.sendall(createMessage("signal", f"{requestID}", False))
        client2.sendall(createMessage("signal", f"{requestID}", False))

    def option6(self):
        """
        [UNUSED] This method is kept for reference but no longer used in the UI.
        Original function: Send CID
        """
        self.client.sendall(createMessage("info", "RequestsID", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        self.client.sendall(createMessage("info", "CID", True))
        CID = decodeMessage(self.client.recv(1024))["data"]
        
        try:
            self.mergeDB.insertCID(self.username, requestID, CID)
            record_info = {
                "request_id": requestID,
                "cid": CID
            }
            self.client.sendall(createMessage("signal", f"record_my_cid:{json.dumps(record_info)}", False))
            response = decodeMessage(self.client.recv(1024))
            if response["type"] == "info" and "success" in response["data"].lower():
                self.client.sendall(createMessage("info", "CID recorded successfully on server and local database", False))
            else:
                self.client.sendall(createMessage("info", f"CID recorded on server, but client reported: {response['data']}", False))
        except ValueError as e:
            self.client.sendall(createMessage("info", f"{e}", False))

    def option7(self):
        """
        [UNUSED] This method is kept for reference but no longer used in the UI.
        Original function: Upload to IPFS
        """
        self.client.sendall(createMessage("signal", "upload_to_ipfs", False))
        response = decodeMessage(self.client.recv(1024))
        if response["type"] == "info":
            self.client.sendall(createMessage("info", response["data"], False))
        else:
            self.client.sendall(createMessage("info", "Failed to get CID from client", False))

    def option8(self):
        """
        [UNUSED] This method is kept for reference but no longer used in the UI.
        Original function: Get Partner CID
        """
        self.client.sendall(createMessage("info", "Enter RequestID to get partner's CID:", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        
        try:
            data = self.mergeDB.getRequest(requestID)
            request_id, user1_id, user2_id, _, _, user1_cid, user2_cid = data
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
            partner_info = {
                "request_id": requestID,
                "partner_cid": partner_cid
            }
            self.client.sendall(createMessage("signal", f"record_partner_cid:{json.dumps(partner_info)}", False))
            response = decodeMessage(self.client.recv(1024))
            result_info = f"Partner {partner_username}'s CID: {partner_cid}\n"
            if response["type"] == "info" and "success" in response["data"].lower():
                result_info += "This CID has been saved to your local database.\n"
            else:
                result_info += f"Warning: {response['data']}\n"
            result_info += "To retrieve their files: ipfs get " + partner_cid
            self.client.sendall(createMessage("info", result_info, False))
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error: {e}", False))
        except Exception as e:
            self.client.sendall(createMessage("info", f"Unexpected error: {e}", False))

    def option9(self):
        """
        [UNUSED] This method is kept for reference but no longer used in the UI.
        Original function: Download from IPFS
        """
        self.client.sendall(createMessage("info", "Enter the CID to download from IPFS:", True))
        cid = decodeMessage(self.client.recv(1024))["data"]
        if not cid:
            self.client.sendall(createMessage("info", "Error: No CID provided", False))
            return
        self.client.sendall(createMessage("info", "Enter download location (leave blank for default 'Downloaded_Data'):", True))
        download_path = decodeMessage(self.client.recv(1024))["data"]
        if not download_path:
            download_path = "Downloaded_Data"
        download_info = {
            "cid": cid,
            "download_path": download_path
        }
        self.client.sendall(createMessage("signal", f"download_from_ipfs:{json.dumps(download_info)}", False))
        response = decodeMessage(self.client.recv(1024))
        self.client.sendall(createMessage("info", response["data"], False))

    def handle_psi_cid_exchange(self, requestID, cid, step):
        """
        Store the client's CID for the given PSI step and notify the partner.
        """
        try:
            # Store CID in server database
            self.mergeDB.insertCID(self.username, requestID, cid, step)
            
            # Signal client to record their own CID
            record_info = {
                "request_id": requestID,
                "cid": cid
            }
            self.client.sendall(createMessage("signal", f"record_my_cid:{json.dumps(record_info)}", False))
            response = decodeMessage(self.client.recv(1024))
            if response["type"] != "info" or "success" not in response["data"].lower():
                self.client.sendall(createMessage("info", f"Warning: Failed to record CID locally: {response['data']}", False))
            
            # Get partner information
            data = self.mergeDB.getRequest(requestID)
            user1_id, user2_id = data[1:3]
            partner_username = user2_id if self.username == user1_id else user1_id
            
            # Check if partner is online
            if partner_username in LoginUsers._OnlineLoginUsers:
                partner_client = LoginUsers._OnlineLoginUsers[partner_username]
                # Signal partner to record this CID
                partner_info = {
                    "request_id": requestID,
                    "partner_cid": cid
                }
                partner_client.sendall(createMessage("signal", f"record_partner_cid:{json.dumps(partner_info)}", False))
                # Wait for partner's response
                partner_response = decodeMessage(partner_client.recv(1024))
                if partner_response["type"] == "info" and "success" in partner_response["data"].lower():
                    self.client.sendall(createMessage("info", f"CID sent to partner {partner_username} and recorded successfully.", False))
                else:
                    self.client.sendall(createMessage("info", f"CID sent to partner {partner_username}, but they reported: {partner_response['data']}", False))
            else:
                self.client.sendall(createMessage("info", f"Partner {partner_username} is offline. CID stored in server database.", False))
            
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error storing CID: {e}", False))
            return False
        return True

    def psi_protocol(self):
        """
        Menu Option 6: PSI Protocol (Steps 1-4)
        Handles all steps of the Private Set Intersection protocol
        """
        # Ask which step to run
        if self.last_request_id:
            next_step = min(self.last_psi_step, 4)
            self.client.sendall(createMessage("info", f"Which PSI step do you want to run? (1-4) (press Enter for step {next_step}):", True))
            step_str = decodeMessage(self.client.recv(1024))["data"]
            step = next_step if step_str.strip() == "" else int(step_str)
        else:
            self.client.sendall(createMessage("info", "Which PSI step do you want to run? (1-4):", True))
            step_str = decodeMessage(self.client.recv(1024))["data"]
            try:
                step = int(step_str)
                if step < 1 or step > 4:
                    raise ValueError("Step must be between 1 and 4")
            except ValueError:
                self.client.sendall(createMessage("info", "Invalid step number. Please enter a number between 1 and 4.", False))
                return

        # Run the appropriate step
        if step == 1:
            self.__run_psi_step1()
        else:
            self.__run_psi_step_continuation(step)

    def __run_psi_step1(self):
        """
        Run PSI Protocol Step 1: Initialize and compute first blinded values
        Internal method called by psi_protocol
        """
        # Ask for RequestID
        self.client.sendall(createMessage("info", "Enter RequestID for PSI protocol:", True))
        requestID = decodeMessage(self.client.recv(1024))["data"]
        
        # Store the requestID for future use
        self.last_request_id = requestID
        # Reset step to 1 when starting a new protocol
        self.last_psi_step = 1
        
        try:
            data = self.mergeDB.getRequest(requestID)
            user1_id, user2_id, user1_confirm, user2_confirm = data[1:5]
            if not (user1_confirm and user2_confirm):
                self.client.sendall(createMessage("info", "Request hasn't been confirmed by both parties", False))
                return
            if self.username not in [user1_id, user2_id]:
                self.client.sendall(createMessage("info", "You are not part of this merge request", False))
                return
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error: {e}", False))
            return
        
        # Ask for Excel file path
        self.client.sendall(createMessage("info", "Enter Excel file path:", True))
        excel_path = decodeMessage(self.client.recv(1024))["data"]
        
        # Ask for identifier columns
        self.client.sendall(createMessage("info", "Enter identifier columns (comma-separated, e.g. 's_id,p_id,s_sex'):", True))
        id_columns_str = decodeMessage(self.client.recv(1024))["data"]
        id_columns = [col.strip() for col in id_columns_str.split(',')]
        
        # Ask for data columns
        self.client.sendall(createMessage("info", "Enter data columns to share (comma-separated, e.g. 'county,region'):", True))
        data_columns_str = decodeMessage(self.client.recv(1024))["data"]
        data_columns = [col.strip() for col in data_columns_str.split(',')]
        
        # Generate deterministic prime from requestID
        prime = generate_deterministic_prime(requestID)
        
        # Generate private key from the prime
        private_key = random.randint(2, prime-2)
        
        # Create PSI parameters
        psi_params = {
            "excel_path": excel_path,
            "id_columns": id_columns,
            "data_columns": data_columns,
            "private_key": private_key,
            "prime": prime,
            "request_id": requestID
        }
        
        # Send signal to client to start PSI protocol
        self.client.sendall(createMessage("signal", f"psi_start:{json.dumps(psi_params)}", False))
        
        # Wait for client's response with CID
        response = decodeMessage(self.client.recv(1024))
        
        if response["type"] == "info" and "CID:" in response["data"]:
            cid = response["data"].split("CID: ")[1].strip()
            # Handle CID exchange
            if self.handle_psi_cid_exchange(requestID, cid, 1):
                self.client.sendall(createMessage("info", f"PSI Step 1 completed. CID: {cid}\nWaiting for partner's CID to proceed to Step 2.", False))
                # Increment step for next operation
                self.last_psi_step = 2
            else:
                self.client.sendall(createMessage("info", "Failed to handle CID exchange.", False))
        else:
            self.client.sendall(createMessage("info", f"Failed to start PSI protocol: {response['data']}", False))

    def __run_psi_step_continuation(self, step):
        """
        Run PSI Protocol Steps 2-4: Continue the protocol with subsequent steps
        Internal method called by psi_protocol
        
        Args:
            step: Which step of the protocol to run (2-4)
        """
        # If we have a previous request ID, offer it as default
        if self.last_request_id:
            self.client.sendall(createMessage("info", f"Enter RequestID for PSI protocol (press Enter to use last ID: {self.last_request_id}):", True))
            input_id = decodeMessage(self.client.recv(1024))["data"]
            requestID = self.last_request_id if input_id.strip() == "" else input_id
            # Update the stored request ID
            self.last_request_id = requestID
        else:
            # Ask for RequestID as usual
            self.client.sendall(createMessage("info", "Enter RequestID for PSI protocol:", True))
            requestID = decodeMessage(self.client.recv(1024))["data"]
            self.last_request_id = requestID
        
        try:
            data = self.mergeDB.getRequest(requestID)
            user1_id, user2_id, user1_confirm, user2_confirm = data[1:5]
            if not (user1_confirm and user2_confirm):
                self.client.sendall(createMessage("info", "Request hasn't been confirmed by both parties", False))
                return
            if self.username not in [user1_id, user2_id]:
                self.client.sendall(createMessage("info", "You are not part of this merge request", False))
                return
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error: {e}", False))
            return
        
        # Check if partner has uploaded CID for previous step
        try:
            partner_cid = self.mergeDB.getPartnerCID(self.username, requestID, step-1)
            if not partner_cid:
                self.client.sendall(createMessage("info", f"Partner has not uploaded CID for Step {step-1} yet.", False))
                return
            # Signal client to record partner's CID
            partner_info = {
                "request_id": requestID,
                "partner_cid": partner_cid
            }
            self.client.sendall(createMessage("signal", f"record_partner_cid:{json.dumps(partner_info)}", False))
            response = decodeMessage(self.client.recv(1024))
            if response["type"] != "info" or "success" not in response["data"].lower():
                self.client.sendall(createMessage("info", f"Failed to record partner's CID: {response['data']}", False))
                return
        except ValueError as e:
            self.client.sendall(createMessage("info", f"Error retrieving partner's CID: {e}", False))
            return
        
        # Send signal to client to continue PSI protocol
        signal_type = f"psi_step{step}:{partner_cid}"
        self.client.sendall(createMessage("signal", signal_type, False))
        
        # Wait for client's response
        response = decodeMessage(self.client.recv(1024))
        
        if response["type"] == "info" and "CID:" in response["data"]:
            cid = response["data"].split("CID: ")[1].strip()
            # Handle CID exchange
            if self.handle_psi_cid_exchange(requestID, cid, step):
                if step < 4:
                    self.client.sendall(createMessage("info", f"PSI Step {step} completed. CID: {cid}\nWaiting for partner's CID to proceed to Step {step+1}.", False))
                    # Increment step for next operation
                    self.last_psi_step = step + 1
                else:
                    self.client.sendall(createMessage("info", f"PSI Step {step} completed. Final result saved: {response['data'].split('saved to: ')[1]}", False))
                    # Reset step after completing the protocol
                    self.last_psi_step = 1
            else:
                self.client.sendall(createMessage("info", "Failed to handle CID exchange.", False))
        else:
            if step != 4:
                self.client.sendall(createMessage("info", f"Failed to execute PSI step {step}: {response['data']}", False))

    def __del__(self):
        pass