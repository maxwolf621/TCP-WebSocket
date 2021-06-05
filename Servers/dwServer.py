import socket
import threading
import queue
import time
import sys, os
from netapi2 import *
import logging
import json
import select
ENCODING = 'utf-8'
BUFFSIZE = 1024
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
'''
this is dwServer that do the following main process:
        by threads of listener , receiver , sender
        1.receiver :
            receive()    :to receive the data from client and pass it to psrrecvData()
            psrrecvData():to analyze the data 
                the anaylized data would give information of the followings 
                1.Location/path of filename of dowloading 
                2.Directory for savingPath
                3.Name of Sender(request) , Receiver(Who uploaded the file)
                these would all push into queue               
        2.sender :
            send()        :
                    check the queue, then pop them and pass them to sendtoTarget
            sendtoTarget():
                    sned file via class NetAPI.send_file(file,savingpath)
            
    plus*You could enter "q" from Keyboard in the terminal that allow 
         user who is as manager of dwServeer to quite the dwServer
'''

class dwServer(threading.Thread):
    def __init__(self, host = "127.0.0.1", port = 5780):
        super().__init__(daemon=False, target=self.run)
        try:
            self.host = str(host)
            self.port = int(port)
        except ValueError as e:
            print(e)
        #set TCP network
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socketList = []
        self.userList = {}
        self.queueSendFile = queue.Queue()
        self.shutdown = False
        self.errorcount = 0
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen(3)
            self.sock.setblocking(False)
        except socket.error:
            self.shutdown = True
        if not self.shutdown:
            '''
            with 3 threads : 
                1.listener (make a connection with client.py)
                2.reciever (recv request from client.py <users>)
                3.sender (send file to client.py <users>)
            '''
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
                self.sock_sendFile = NetAPI(connection)
                connection.setblocking(False)
                if connection not in self.socketList:
                    self.socketList.append(connection)
            except socket.error:
                pass
            finally:
                self.lock.release()
            time.sleep(0.050)
    
    def receive(self):
        '''recv the request for download a file from client'''
        logging.info('[DEBUG] RECEIVER Thread START')
        while True:
            if len(self.socketList) > 0:
                for connection in self.socketList:
                    try:
                        self.lock.acquire()
                        data = connection.recv(BUFFSIZE)
                    except socket.error:
                        data = None
                    finally:
                        self.lock.release()
                    self.psrrecvData(data, connection)
    
    #Empfangen zu analysieren
    def psrrecvData(self, data, connection):
        '''
            arg `data` that includes [request,user,target,filename,savingpath]:
            To analyze it to get a location of file then insert into message[4]

            if we combine the elements alltogether in the message would look like\
                 as the following      
            1. download file from private chatroom => file/{target}{user}/filename
            2. upload file from public  chatroom   => file/Public/filename
        '''
        if data:
            message = data.decode(ENCODING)
            message = message.split(";")
            
            # Analyze the information of message
            # message[2] : user name 
            # message[1] : request 
            if message[0] == 'request' and message[2] != 'all' :
                ''' message recv from client and send to other specified client '''
                file = f'file/{message[2]}{message[1]}/{message[3]}'
                savingpath = message[4]
                self.queueSendFile.put((file,savingpath))
            # otherwise message[2] is all 
            else:
                file = f'file/Public/{message[3]}'
                savingpath = message[4]
                self.queueSendFile.put((file,savingpath))

    def send(self):
        '''Exceute `SENDING FILE` '''
        logging.info('[DEBUG] SENDER Thread START')
        while True:
            if not self.queueSendFile.empty():
                file, savingpath = self.queueSendFile.get()
                logging.debug(f'[DEBUG] Get File : {file} and Savingpath:{savingpath} Successfully')
                self.sendtoTarget(file, savingpath)
                if self.errorcount !=0:
                    logging.debug(f'[DEBUG] fail to Send File ')
                    self.errorcount = 0
                    logging.debug(f'[DEBUG] Send File : {file} and Savingpath:{savingpath} Successfully')
                self.queueSendFile.task_done()
            else:
                time.sleep(0.05)
    def sendtoTarget(self,file,savingpath):
        """Send specified file to user who requests this file"""
        try:
            self.lock.acquire()
            self.sock_sendFile.send_file(file,savingpath)
        except AttributeError as e:
            logging.info(f'[WARNING] CHECK YOUR SOCKET {e}')
        except FileNotFoundError as e:
            self.errorcount =1
            logging.info(f'[WARNING] CHECK DIRECTORY {e}')
        finally:
            self.lock.release()

if __name__ == '__main__':
    try:
        #host = sys.argv[1]
        #port = int(sys.argv[2])
        server = dwServer()
    except IndexError as e:
        print(e)
    except OSError as e:
        print(e)

