
import socket
import json
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
                message = createMessage("response",payload, False)
                if payload.lower() == "exit":
                    print("Closing connection.")
                    break
                client.send(json.dumps(message).encode())
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