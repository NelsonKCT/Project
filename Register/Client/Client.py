
import socket

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
            print(f"Server: {data}")

            # Sending data to the server
            message = input()
            if message.lower() == "exit":
                print("Closing connection.")
                break
            client.send(message.encode())
    except KeyboardInterrupt:
        print("\nConnection interrupted by user.")
    finally:
        client.close()

if __name__ == "__main__":
    main()