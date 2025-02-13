import subprocess
import time
import os

# File paths
server_file = "Server\Server.py"
client_file = "Client\Client.py"

def run_server():
    # Open server in a new command-line window
    subprocess.Popen(
        ["start", "cmd", "/k", f"python {server_file}"],
        shell=True,
        
    )

def run_client():
    # Open client in a new command-line window
    subprocess.Popen(
        ["start", "cmd", "/k", f"python {client_file}"],
        shell=True,  # Change to client directory
    )
    print("Client started...")

def main():
    # Start the server
    run_server()
    # Wait for the server to initialize
    time.sleep(2)
    # Start the client
    run_client()

if __name__ == "__main__":
    main()