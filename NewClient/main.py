from C_Client import Client
import threading
def main():
    client = Client("127.0.0.1", 8888)
    client.connect()
    threading.Thread(target= client.receive,daemon=True).start()
    while True:
        try :
            client.logic()
            client.signal_handling()
        except KeyboardInterrupt:
            print("Ending...")
            client.socket.close()
            break
    return
if __name__ =='__main__':
    main()
