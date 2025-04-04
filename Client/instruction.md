# File Encryption and IPFS Upload

This package provides tools for encrypting Excel files, uploading them to IPFS, and sending the resulting Content Identifier (CID) to a server.

## Prerequisites

1. Install IPFS:
   - Download and install from https://docs.ipfs.io/install/
   - Initialize IPFS: `ipfs init`
   - Start the IPFS daemon: `ipfs daemon`


## Usage

### 1. `encrypt_file.py`

(base) nelsonkct@guojiantingdeMacBook-Pro Project % python Client/encrypt.py 
File Encryption Tool
====================
Please enter the name of the file you want to encrypt (from Test_Data/): test_data_1.xlsx
Test_Data/test_data_1.xlsx
File encrypted successfully: Encrypted_Data/encrypted_test_data_1.xlsx
Encryption complete. Encrypted file: Encrypted_Data/encrypted_test_data_1.xlsx

### 2. `upload_to_ipfs.py`

(base) nelsonkct@guojiantingdeMacBook-Pro Project % python Client/upload_to_ipfs.py 
IPFS Upload Tool
===============
IPFS daemon is already running
Please enter the path to the file you want to upload to IPFS: Encrypted_Data/encrypted_test_data_1.xlsx
File uploaded to IPFS with CID: QmQ712j98ChERenxUKhns6dnsPjN8EHKqw92WdFy2h2Csy
Do you want to send the CID to the server? (y/n): y
Enter server host (default: 127.0.0.1): 
Enter server port (default: 8888): 
CID sent to server successfully: QmQ712j98ChERenxUKhns6dnsPjN8EHKqw92WdFy2h2Csy
Server response: hi
CID sent to server successfully

Summary:
1. File: Encrypted_Data/encrypted_test_data_1.xlsx
2. IPFS Content ID: QmQ712j98ChERenxUKhns6dnsPjN8EHKqw92WdFy2h2Csy
3. To retrieve file: ipfs cat QmQ712j98ChERenxUKhns6dnsPjN8EHKqw92WdFy2h2Csy