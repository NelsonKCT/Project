from Server import Server
import threading
def main():
    print('server Starting ...')
    server = Server('127.0.0.1', 8888)
    threading.Thread(target = server.serverThread,daemon=True).start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server shutting down")
        return

if __name__ == "__main__":
    main()