import socket
import json
import os
import importlib.util
import subprocess
import tempfile
import time

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(("127.0.0.1", 8888))
        print("Connected to the server.")
    except ConnectionRefusedError:
        print("Connection failed. Is the server running?")
        return
    
    # Dictionary to store PSI context between steps
    psi_context = {}
    
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
                elif parsed_data['data'].startswith("record_my_cid:"):
                    try:
                        # Extract record info from the signal
                        record_info = json.loads(parsed_data['data'].split(":", 1)[1])
                        request_id = record_info['request_id']
                        cid = record_info['cid']
                        
                        # Import the id_database module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        db_path = os.path.join(current_dir, "id_record.db")
                        db_module_path = os.path.join(current_dir, "id_database.py")
                        spec = importlib.util.spec_from_file_location("id_database", db_module_path)
                        db_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(db_module)
                        
                        # Create database connection and record CID
                        local_db = db_module.LocalDBManager(db_path)
                        local_db.record_my_cid(request_id, cid)
                        local_db.close()
                        
                        response = createMessage("info", "Successfully recorded CID in local database", False)
                        client.send(json.dumps(response).encode())
                    except Exception as e:
                        error_msg = f"Failed to record CID in local database: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("record_partner_cid:"):
                    try:
                        # Extract record info from the signal
                        record_info = json.loads(parsed_data['data'].split(":", 1)[1])
                        request_id = record_info['request_id']
                        partner_cid = record_info['partner_cid']
                        
                        # Import the id_database module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        db_path = os.path.join(current_dir, "id_record.db")
                        db_module_path = os.path.join(current_dir, "id_database.py")
                        spec = importlib.util.spec_from_file_location("id_database", db_module_path)
                        db_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(db_module)
                        
                        # Create database connection and record partner CID
                        local_db = db_module.LocalDBManager(db_path)
                        local_db.record_partner_cid(request_id, partner_cid)
                        local_db.close()
                        
                        response = createMessage("info", "Successfully recorded partner CID in local database", False)
                        client.send(json.dumps(response).encode())
                    except Exception as e:
                        error_msg = f"Failed to record partner CID in local database: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("psi_start:"):
                    try:
                        # Extract PSI parameters 
                        psi_params = json.loads(parsed_data['data'].split(":", 1)[1])
                        
                        # Import the PSI module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        psi_module_path = os.path.join(current_dir, "psi_dh.py")
                        spec = importlib.util.spec_from_file_location("psi_dh", psi_module_path)
                        psi_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(psi_module)
                        
                        # Create output directory for PSI files
                        output_dir = os.path.join(current_dir, "psi_output")
                        os.makedirs(output_dir, exist_ok=True)
                        
                        # Execute PSI step 1
                        excel_path = psi_params["excel_path"]
                        id_columns = psi_params["id_columns"]
                        private_key = psi_params["private_key"]
                        prime = psi_params["prime"]
                        
                        result = psi_module.run_psi_protocol(
                            excel_path=excel_path,
                            id_columns=id_columns,
                            data_columns=psi_params.get("data_columns", []),
                            private_key=private_key,
                            prime=prime,
                            output_dir=output_dir,
                            step=1
                        )
                        
                        # Store context for later steps
                        psi_context["excel_path"] = excel_path
                        psi_context["id_columns"] = id_columns
                        psi_context["data_columns"] = psi_params.get("data_columns", [])
                        psi_context["private_key"] = private_key
                        psi_context["prime"] = prime
                        psi_context["output_dir"] = output_dir
                        
                        # Return CID to the server
                        cid = result["step1"]["cid_c"]
                        response = createMessage("info", f"PSI Step 1 completed. CID: {cid}", False)
                        client.send(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_msg = f"Failed to execute PSI step 1: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("psi_step2:"):
                    try:
                        # Extract partner's CID
                        partner_cid = parsed_data['data'].split(":", 1)[1]
                        
                        # Import the PSI module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        psi_module_path = os.path.join(current_dir, "psi_dh.py")
                        spec = importlib.util.spec_from_file_location("psi_dh", psi_module_path)
                        psi_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(psi_module)
                        
                        # Check if all required context exists
                        if not all(k in psi_context for k in ["excel_path", "id_columns", "data_columns", "private_key", "prime", "output_dir"]):
                            # Try to load from config file if available
                            output_dir = os.path.join(current_dir, "psi_output")
                            psi_config_file = os.path.join(output_dir, "psi_config.json")
                            if os.path.exists(psi_config_file):
                                with open(psi_config_file, 'r') as f:
                                    config = json.load(f)
                                    psi_context["excel_path"] = config.get("excel_path")
                                    psi_context["id_columns"] = config.get("id_columns")
                                    psi_context["data_columns"] = config.get("data_columns")
                                    psi_context["private_key"] = config.get("private_key")
                                    psi_context["prime"] = config.get("prime")
                                    psi_context["output_dir"] = output_dir
                        
                        # Execute PSI step 2
                        result = psi_module.run_psi_protocol(
                            excel_path=psi_context.get("excel_path", ""),
                            id_columns=psi_context.get("id_columns", []),
                            data_columns=psi_context.get("data_columns", []),
                            private_key=psi_context.get("private_key", 0),
                            prime=psi_context.get("prime", 0),
                            output_dir=psi_context.get("output_dir", output_dir),
                            partner_cid_c=partner_cid,
                            step=2
                        )
                        
                        # Return CID to the server
                        cid = result["step2"]["cid_k"]
                        response = createMessage("info", f"PSI Step 2 completed. CID: {cid}", False)
                        client.send(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_msg = f"Failed to execute PSI step 2: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("psi_step3:"):
                    try:
                        # Extract partner's CID
                        partner_cid = parsed_data['data'].split(":", 1)[1]
                        
                        # Import the PSI module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        psi_module_path = os.path.join(current_dir, "psi_dh.py")
                        spec = importlib.util.spec_from_file_location("psi_dh", psi_module_path)
                        psi_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(psi_module)
                        
                        # Check if all required context exists
                        if not all(k in psi_context for k in ["excel_path", "id_columns", "data_columns", "private_key", "prime", "output_dir"]):
                            # Try to load from config file if available
                            output_dir = os.path.join(current_dir, "psi_output")
                            psi_config_file = os.path.join(output_dir, "psi_config.json")
                            if os.path.exists(psi_config_file):
                                with open(psi_config_file, 'r') as f:
                                    config = json.load(f)
                                    psi_context["excel_path"] = config.get("excel_path")
                                    psi_context["id_columns"] = config.get("id_columns")
                                    psi_context["data_columns"] = config.get("data_columns")
                                    psi_context["private_key"] = config.get("private_key")
                                    psi_context["prime"] = config.get("prime")
                                    psi_context["output_dir"] = output_dir
                        
                        # Execute PSI step 3
                        result = psi_module.run_psi_protocol(
                            excel_path=psi_context.get("excel_path", ""),
                            id_columns=psi_context.get("id_columns", []),
                            data_columns=psi_context.get("data_columns", []),
                            private_key=psi_context.get("private_key", 0),
                            prime=psi_context.get("prime", 0),
                            output_dir=psi_context.get("output_dir", output_dir),
                            partner_cid_k=partner_cid,
                            step=3
                        )
                        
                        # Return CID to the server
                        cid = result["step3"]["cid_match"]
                        response = createMessage("info", f"PSI Step 3 completed. CID: {cid}", False)
                        client.send(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_msg = f"Failed to execute PSI step 3: {str(e)}"
                        response = createMessage("info", error_msg, False)
                        client.send(json.dumps(response).encode())
                elif parsed_data['data'].startswith("psi_step4:"):
                    try:
                        # Extract partner's CID
                        partner_cid = parsed_data['data'].split(":", 1)[1]
                        
                        # Import the PSI module
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        psi_module_path = os.path.join(current_dir, "psi_dh.py")
                        spec = importlib.util.spec_from_file_location("psi_dh", psi_module_path)
                        psi_module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(psi_module)
                        
                        # Check if all required context exists
                        if not all(k in psi_context for k in ["excel_path", "id_columns", "data_columns", "private_key", "prime", "output_dir"]):
                            # Try to load from config file if available
                            output_dir = os.path.join(current_dir, "psi_output")
                            psi_config_file = os.path.join(output_dir, "psi_config.json")
                            if os.path.exists(psi_config_file):
                                with open(psi_config_file, 'r') as f:
                                    config = json.load(f)
                                    psi_context["excel_path"] = config.get("excel_path")
                                    psi_context["id_columns"] = config.get("id_columns")
                                    psi_context["data_columns"] = config.get("data_columns")
                                    psi_context["private_key"] = config.get("private_key")
                                    psi_context["prime"] = config.get("prime")
                                    psi_context["output_dir"] = output_dir
                        
                        # Execute PSI step 4
                        result = psi_module.run_psi_protocol(
                            excel_path=psi_context.get("excel_path", ""),
                            id_columns=psi_context.get("id_columns", []),
                            data_columns=psi_context.get("data_columns", []),
                            private_key=psi_context.get("private_key", 0),
                            prime=psi_context.get("prime", 0),
                            output_dir=psi_context.get("output_dir", output_dir),
                            partner_cid_match=partner_cid,
                            step=4
                        )
                        
                        # Final result file path
                        final_file_path = result["step4"]["final_file_path"]
                        response = createMessage("info", f"PSI Protocol completed. Final result saved to: {final_file_path}", False)
                        client.send(json.dumps(response).encode())
                        
                    except Exception as e:
                        error_msg = f"Failed to execute PSI step 4: {str(e)}"
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