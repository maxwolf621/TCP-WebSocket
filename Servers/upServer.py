import socket
import threading
from APIS.netapi2 import *
import logging


'''
    This is a Server for uploading the file into `... /file/ ..`  directory
    Main Functions by Following :
    1. listen()  connects with client
    2. reciver() receives the file from client and store  \
        the received file in the directory
'''
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=False, target=self.run)
        try:
            self.host = str(host)
            self.port = int(port)
        except ValueError as e:
            print(e)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketsList = []
        self.path = None
        self.shutdown = False
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(3)
        except socket.error:
            self.shutdown = True
        if not self.shutdown:
            listener = threading.Thread(target=self.listen, daemon=True)
            receiver = threading.Thread(target=self.receive, daemon=True)
            self.lock = threading.RLock()
            listener.start()
            receiver.start()
            self.start()

    def run(self):
        while not self.shutdown:
            message = input('enter q to exit:>>')
            if message == "q" :
                self.sock.close()
                self.shutdown = True

    def listen(self):
        logging.info('[DEBUG] LISTEN Thread START')
        while True:
            self.lock.acquire()
            sock, addr = self.sock.accept()
            logging.info(f"[SOCKET] NEW {sock}")
            if sock not in self.socketsList:
                self.socketsList.append(sock)
            self.lock.release()
            time.sleep(0.05)

    def receive(self):
        logging.info('[DEBUG] RECEIVER Thread START')
        while True:
            if len(self.socketsList) > 0:           
                for sock in self.socketsList:
                    handle = NetAPI(sock)
                    while True:
                        data = handle.recv_file()
                        if not data:
                            break
                        check = handle.save_file(data.get('FILEPATH'))
                        logging.debug(f"Save successfully ? {check}")
                    sock.close()
                    self.socketsList.remove(sock)
                    
                    
if __name__ == '__main__':
    try:
        #host = sys.argv[1]
        #port = int(sys.argv[2])
        server = Server(host="127.0.0.1", port=5770)
    except IndexError as e:
        print(e)
    except OSError as e:
        print(e)
