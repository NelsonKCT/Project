import subprocess
import time
import os
import sys
import shlex

# File paths
server_file = "/Users/nelsonkct/Documents/Project/Register/Server/Server.py"
client_file = "/Users/nelsonkct/Documents/Project/Register/Client/Client.py"

# 獲取當前 Python 解釋器的路徑
python_exe = sys.executable

def run_server():
    # Build the command with safely quoted paths
    cmd = f"{shlex.quote(python_exe)} {shlex.quote(server_file)}"
    apple_script = f'tell application "Terminal" to do script "{cmd}"'
    subprocess.Popen(["osascript", "-e", apple_script])

def run_client():
    # Build the command with safely quoted paths
    cmd = f"{shlex.quote(python_exe)} {shlex.quote(client_file)}"
    apple_script = f'tell application "Terminal" to do script "{cmd}"'
    subprocess.Popen(["osascript", "-e", apple_script])
    print("Client started...")

def main():
    # Start the server
    run_server()
    # Wait for the server to initialize
    time.sleep(2)
    # Start the client
    run_client()
    run_client()

if __name__ == "__main__":
    main()