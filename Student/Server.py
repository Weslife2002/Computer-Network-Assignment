import socket
import threading
import sys
from ServerWorker import ServerWorker


class Server:

    def main(self):
        SERVER_PORT = int(sys.argv[1])  # 5050
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SERVER_IP = socket.gethostbyname(socket.gethostname())
        rtspSocket.bind((SERVER_IP, SERVER_PORT))
        print(f"[LISTENING] Listen for clients' connection on {(SERVER_IP, SERVER_PORT)} ...")
        rtspSocket.listen(5)

        # Receive client info (address,port) through RTSP/TCP session
        while True:
            clientInfo = {}
            clientInfo['rtspSocket'] = rtspSocket.accept()
            ServerWorker(clientInfo).run()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            print(clientInfo['rtspSocket'][0])


if __name__ == "__main__":
    (Server()).main()
