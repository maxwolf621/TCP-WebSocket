import socket
import threading
import queue
import time
import sys, os
from APIS.netapi2 import *   #error record 
import logging
import json

CODE = 'utf-8'
BUFFSIZE = 1024
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

'''
    this is ChatServer that does the following main process:
    by threads of listener , receiver , sender
    1. receiver :
        via receiver() to receive data from client and pass to psrrecvData() to analyze the type of message
    2. sender :
        via send() which ChatServer puts the message that function pesrrecvData() has analyzed into it
            process two options:
            1.Send to broadcast
            2.Send to Specified User
    3.
    updateLoginUsersList : broadcast to all clients that current online userlist
    updateFilesList      :broadcast to all clients that current FilesList in dir (file/Public)
    updatePrivateFilesList: send the current FilesList in the specified dir to the User that Ask for it
    
    plus*
    You could enter "q" from Keyboard in the terminal that allow \
        user who is as manager of ChatServer to quite the ChatServer
'''

class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=False, target=self.run)
        try:
            self.host = str(host)
            self.port = int(port)
        except ValueError as e:
            print(e)
            
        self.path = 'file/Public'
        #set TCP network
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketList = []
        self.userList = {}
        self.queue = queue.Queue()  
        self.shutdown = False
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(3)
            self.sock.setblocking(False)
        except socket.error:
            self.shutdown = True

        if not self.shutdown:
            listener = threading.Thread(target=self.listen, daemon=True)
            receiver = threading.Thread(target=self.receive, daemon=True)
            sender = threading.Thread(target=self.send, daemon=True)
            self.lock = threading.RLock()

            listener.start()
            receiver.start()
            sender.start()
            self.start()

    def run(self):
        print("enter q to exit")
        while not self.shutdown:
            try:
                message = input()
                if message == "q" :
                    self.sock.close()
                    self.shutdown = True
            except RuntimeError as e:
                print(e.args)

    def listen(self):
        logging.info('[DEBUG] LISTEN Thread START')
        while True:
            try:
                self.lock.acquire()
                connection, address = self.sock.accept()
                connection.setblocking(False)
                if connection not in self.socketList:
                    self.socketList.append(connection)
            except socket.error:
                pass
            finally:
                self.lock.release()
            time.sleep(0.050)
    #recv from Client
    def receive(self):
        logging.info('[DEBUG] RECEIVER Thread START')
        while True:
            if len(self.socketList) > 0:
                for connection in self.socketList:
                    try:
                        self.lock.acquire()
                        data = connection.recv(BUFFSIZE)
                        #logging.debug('[DEBUG] receiving data from Client Successfully')
                    except socket.error:
                        data = None
                    finally:
                        self.lock.release()
                    self.psrrecvData(data, connection)

    def send(self):
        logging.info('[DEBUG] SENDER Thread START')
        while True:
            if not self.queue.empty():
                #get user_targer
                target, origin, data = self.queue.get()
                if target == 'broadcast':
                    self.Broadcast(origin, data)
                else:
                    self.sendtoTarget(target, data)
                self.queue.task_done()
            else:
                time.sleep(0.05)

    def Broadcast(self, origin, data):
        """Send data to all users except origin"""
        if origin != 'server':
            origin_address = self.userList[origin]
        else:
            origin_address = None
        for connection in self.socketList:
            if connection != origin_address:
                try:
                    self.lock.acquire()
                    connection.send(data)
                except socket.error:
                    self.rmsocketConnection(connection)
                finally:
                    self.lock.release()

    def sendtoTarget(self, target, data):
        """Send data to specified target"""
        targetAddr = self.userList[target]
        try:
            self.lock.acquire()
            targetAddr.send(data)
        except socket.error:
            self.rmsocketConnection(targetAddr)
        finally:
            self.lock.release()

    """Process received data"""
    def psrrecvData(self, data, connection):
        if data:
            '''msg receive from client '''
            message = data.decode(CODE)
            message = message.split(";")
            '''
            message[0] = (it could be msg ,login , logout , fileupdate)
            message[1] = User(sender)
            message[2] = Target (receiver)
            message[3] = message from sender
            '''
            print(message[0])
            if message[0] == 'login':
                tmp_login = message[1]
                # if create name is already existing
                while message[1] in self.userList:
                    message[1] += '#'
                if tmp_login != message[1]:
                    prompt = f'broadcast;server;{message[1]}; UserName {tmp_login} already in use.Your login changed to{message[1]}\n'
                    self.queue.put((message[1], 'server', prompt.encode(CODE)))
                #dictionary user : connection
                self.userList[message[1]] = connection
                print(message[1] + ' has Joined the Chat Room')
                self.updateLoginUsersList()
            elif message[0] == 'logout':
                self.socketList.remove(self.userList[message[1]])
                if message[1] in self.userList:
                    del self.userList[message[1]]
                print(message[1] + ' has Left')
                self.updateLoginUsersList()
            elif message[0] == 'fileupdate':
                logging.debug('[DEBUG] Reqeust Of Public File Update is Receiving')
                self.updateFilesList()
            elif message[0] == 'privatefileUpdate':
                logging.debug('[DEBUG] Request Of Private File Update is Receiving ')
                receiver = message[1]
                sender = message[2]
                logging.debug(f'[DEBUG] receiver is {receiver}')
                self.updatePrivateFilesList(receiver,sender)
            elif message[0] == 'msg' :
                ''' message recv from client and send to other specified client ''' 
                msg = data.decode(CODE) + '\n'
                data = msg.encode(CODE)
                # message[2] : target (specified client)
                self.queue.put((message[2], message[1], data))
            elif message[0] == 'broadcast':
                ''' recv msg of broadcast from clients'''
                msg = data.decode(CODE) + '\n'
                data = msg.encode(CODE)
                self.queue.put((message[0], message[1], data))                         
            

    def rmsocketConnection(self, connection):
        """Remove connection from server's connection list"""
        self.socketList.remove(connection)
        for login, address in self.userList.items():
            if address == connection:
                del self.userList[login]
                break
        self.updateLoginUsersList()

    def updateLoginUsersList(self):
        """Update list of active users"""
        logins = 'login'
        for login in self.userList:
            print(login)
            logins +=  ';' + login
            print(logins)
        logins += ';all\n'
        #(broadcast , server , message<send to receiver>)
        self.queue.put(('broadcast', 'server', logins.encode(CODE)))
    def updateFilesList(self):
        listdir = os.listdir(self.path)
        strdir = json.dumps(listdir)
        files ='fileUpdate;'
        files += strdir +'\n'
        files.encode(CODE)
        logging.info(f'[SHOW] {files} are/is ENCODED utf-8')
        self.queue.put(('broadcast', 'server', files.encode(CODE)))
    
    # receiver : user that may download file
    # sender   : user that upload file
    def updatePrivateFilesList(self,receiver,sender):
        pfile = f'file/{sender}{receiver}'
        if not os.path.exists(pfile):
            os.makedirs(pfile)
        listdir = os.listdir(pfile)
        strdir = json.dumps(listdir)
        files = 'privatefileUpdate;'
        files += strdir + '\n'
        files.encode(CODE)
        logging.debug(f'[DEBUG] receiver : {receiver} , sender : {sender} ')
        logging.debug(f'[DEBUG] {files} are/is ENCODED utf-8 successfully')
        self.queue.put((receiver, sender, files.encode(CODE)))

        
# Create new server with (IP, port)
if __name__ == '__main__':
    try:
        #host = sys.argv[1]
        #port = int(sys.argv[2])
        server = Server(host="127.0.0.1", port=5757)
        #filerserver = fileServer(host,port+1)
    except IndexError as e:
        print(e)