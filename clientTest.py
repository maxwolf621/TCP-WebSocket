from windows import *
import socket
import time
import select
import queue
import logging
from netapi2 import NetAPI
from caser import *
import json
'''
    this is client which you need to activate it via **terminal**
    it will also activate windows.py (GUI inteface)
    
    functions of Client
    1. connect upload Server 
        you could upload file by clicking the button right bottom of Chatwindow 
    2. connect download Server
        tou could download files from file on right side of Chatwindow 
    3. connect Chat Server
        by following functions the Chat Server can supply 
        1.send message to communication with private or public ChatWindow
        
        by notifyServer() you could
        1.update filelist
        2.update userlist
    4. Using run() via select() to process send, receive , exceptional
        
'''
logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
#DEFINE
CODE = 'utf-8'
buffSize = 2048

class Client(threading.Thread):
    def __init__(self, host="127.0.0.1", port=5757 , portFile =5770, portGetFile=5780):
        super().__init__(daemon=True, target=self.run)
        try:
            self.host = str(host)
            self.port = int(port)
            self.portFile = int(portFile)
            self.portGetFile=int(portGetFile)
        except ValueError:
            logging.info("[WARNING] Probably you enter a negative integer, unreadable string..")
        
        # initilize Socket
        self.connected                 = self.toServer()
        self.connectedGetFileServer    = self.toGetFileServer()
        
        # initilize queque
        self.queueSerChat     = queue.Queue() #Store information for chatServer
        self.queueToUpSer = queue.Queue()     #Store information of the upload file 
        self.queueToDwSer = queue.Queue()     #Store information of the downnload file
        self.lock = threading.RLock()
 
        if self.connected:
            # thread runDowloadSer runs connection with dwServer.py
            runDownloadSer = threading.Thread(target=self.runDownloadServer, daemon=True)
            runUploaderSer = threading.Thread(target=self.)
            # GUI interface
            self.gui = GUI(self)
            
            runDownloadSer.start()
            self.gui.start()
            self.start()
            logging.info('[SHOW] Processing for Connecting Server Successfully')
    
    def toServer(self):
        '''create socket for chatServer'''
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect( (self.host, self.port))
        except ConnectionRefusedError as e:
            logging.info(f"[WARNING] CHECK YOUR chatServer.py", e)
            return False
        except NameError as e:
            logging.info(f"[WARNING] Probably Variable Naming or need to import some Modules", e)
            return False
        except socket.gaierror as e:
            logging.info(f"[WARNING] Format: <str> Host , <int> Port", e)
            return False
        except OverflowError as e:
            logging.info(f"[WARNING] OverflowError , {e}")
            return False
        return True
    
    def toGetFileServer(self):
        '''create socket for dwServer'''
        try:
            self.sock_getFile = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock_getFile.connect( (self.host, self.portGetFile))
            self.getFile= NetAPI(self.sock_getFile)
        except ConnectionRefusedError:
            logging.info(f"[WARNING] CHECK YOUR dwServer.py")
            return False
        return True
    
    def runDownloadServer(self):
        socketInformation = [self.sock_getFile]
        outputs           = [self.sock_getFile]
        while socketInformation:
            receive, send, exceptional = select.select(socketInformation, outputs, socketInformation)
            if self.sock_getFile in receive:
                    if self.sock_getFile.getpeername()[1] == self.portGetFile :
                        #with self.lock:
                        try:
                            while True:
                                data = self.getFile.recv_file()
                                if not data :
                                    break
                                check =self.getFile.save_file(data.get('FILEPATH'))
                                logging.info(f'[DEBUG] Save successfully ? {check}')
                                if(check): 
                                    break
                        except socket.error as e:
                            logging.info(f'[WARNING] CHECK SOCKET or dwServer.py {e}')
                            self.sock_getFile.close()
                        #self.lock.release
            if self.sock_getFile in send:
                '''To Request Download Server to download a file from it'''
                if not self.queueToDwSer.empty():
                    try: 
                        data = self.queueToDwSer.get()
                        self.sendRequest(data)
                        self.queueToDwSer.task_done()
                    except socket.error:
                        self.sock.close()
                    except AttributeError as e:
                        logging.info(f'[WARNING] Check Your dwServer is on or not,{e}')
                else:
                    time.sleep(0.05)
            if self.sock_getFile in exceptional:
                #self.gui.display_alert(f'{exceptional}')
                logging.debug(f'[WARNING] {exceptional}')
                self.sock_getFile.close()                
    
    def runUploadSerer(self):
        '''
            To transfer the file to upServer.py
            and upServer.py stores it
        '''
        sock_uploadFile = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_uploadFile.connect( (self.host, self.portFile))
        if not self.queueToUpSer.empty():
            filename,savingpath = self.queueToUpSer.get()
            #logging.debug(f'[DEBUG] get filename->{filename} and savingpath->{savingpath} from queue')
            self.uploadtoupServer(filename,savingpath,sock_uploadFile)
            logging.debug(f'[DEBUG] uploading filename->{filename} and savingpath->{savingpath} from queue')
            self.queueToUpSer.task_done()
            logging.debug('[DEBUG] Task of Queue To Upload Server done! ')
            sock_uploadFile.close() 
        time.sleep(0.05)

    def run(self):
        '''
        run() deals with chatServer.py
        '''
        socketInformation = [self.sock]
        outputs = [self.sock]
        logging.debug(f'Socketinformation : {socketInformation}')
        while socketInformation :
            try:
                # read , write, exceptional 
                receive, send, exceptional = select.select(socketInformation, outputs, socketInformation)
            except ValueError as e :
                logging.info(f'[WARNING] Diconnect from Server, {e}')
                #logging.info(f'[WARNING] Maybe Check Out client.py line 74, {e}')
                logging.info(f'[WARNING] Socket Is Closing')
                self.sock.close()
                break
            if self.sock in receive:
                #logging.debug(f'[DEBUG] self.sock.getpeername() : {self.sock.getpeername()[1]}')
                if self.sock.getpeername()[1] ==self.port:
                    with self.lock:
                        try:
                            data = self.sock.recv(buffSize)
                        except socket.error:
                            print("Socket error")
                            print("Closing ...")
                            self.sock.close()
                            break
                        self.flushCahtWindow(data)
            if self.sock in send:
                #check te queue
                if not self.queueSerChat.empty():
                    try:
                        data = self.queueSerChat.get()
                        self.sendtoServer(data)
                        self.queueSerChat.task_done()
                    except socket.error:
                        self.sock.close()
                    except TypeError as e :
                        print(e.args)
                    except AttributeError as e:
                        print('Check Your chatServer is on or not',e)
            if self.sock in exceptional:
                #self.gui.display_alert(f'{exceptional}')
                logging.debug(f'[WARNING] {exceptional}')
                self.sock.close()
                break

   
    def sendtoServer(self, data):
        '''
        send the message to chatServer
        '''
        with self.lock:
            try:
                self.sock.send(data)
                logging.debug('[DEBUG] Send DATA *MESSAGE* to Server')
            except socket.error:
                self.sock.close()
                self.gui.alertMsgbox('Server error has occurred.')
    def uploadtoupServer(self,filename,savingpath,sock_uploadFile):
        '''For users who upload files to filelistbox'''
        uploadFile= NetAPI(sock_uploadFile)
        return uploadFile.send_file(filename,savingpath)
    
    def sendRequest(self,data):
        '''
        user that download specified file \
            from public or private fileslistbox
        '''
        with self.lock:
            try:
                self.sock_getFile.send(data)
                logging.debug('[DEBUG] Send Request(for downloading) to dwServer')
            except socket.error:
                self.sock_getFile.close()
                self.gui.alertMsgbox('Server error has occurred.')
    
    def flushCahtWindow(self, data):
        '''
        update the ChatWindow displaying
        '''
        if data:
            message = data.decode(CODE).split('\n')
            for msg in message:
                if msg != '':
                    msg = msg.split(';')
                    '''
                    * msg[0] : a header for `broadcast` , `msg` , `login`, `filelistbox update`
                    * msg[1] : user_name
                    * msg[2] : messages
                    '''
                    logging.debug(f'[DEBUG] Flush The ChatWindow with message : *{msg}*')
                    
                    if msg[0] == 'broadcast':
                        text = msg[1] + ' : ' + msg[3] + '\n'
                        self.gui.displayMessage(text)
                        #if msg[2] != self.user and msg[2] != 'all':
                        #self.user = msg[2]
                    elif msg[0] == 'msg':
                        text = msg[1] + ' : ' + msg[3] + '\n'
                        self.gui.displayPrivateMessage(text)
                    elif msg[0] == 'login':
                        '''update listbox of users on ChatWindow '''
                        logging.debug(f'[DEBUG] updating UserList, New User : {msg[1:]} is logining into ChatWindow ')
                        self.gui.mainWindow.updateUsersList(msg[1:])
                    elif msg[0] == 'fileUpdate':
                        '''update filelistbox on publich ChatWindow '''
                        listf =[]
                        for name in json.loads(msg[1]):
                            listf.append(name)
                        logging.debug(f'[DEBUG] Public Files : {listf}')
                        self.gui.mainWindow.updateFilesList(listf)
                    elif msg[0] == 'privatefileUpdate':
                        '''update filelistbox for private chatwindow'''
                        listf=[]
                        for name in json.loads(msg[1]):
                            listf.append(name)
                        if listf == [] :
                            logging.debug(f'[DEBUG] No Files')
                        else:
                            logging.debug(f'[DEBUG] Private Files : {listf}')
                            self.gui.mainWindow.updatePrivateFilesList(listf) 
    
    def notifyServer(self, action, actType):
        '''
        *Put the information of users login/logout into queue \ 
            (to Notify the Server).
        *for notifying Server to update the userListbox \
             and public/private files lists.
        '''
        self.queueSerChat.put(action)
        logging.debug(f'[DEBUG] put {action} into queueSerChat')
        #if actType == "login":
        #    self.user = action.decode(CODE).split(';')[1]
        #elif actType =='fileupdate':
        #    self.file = action.decode(CODE).split(';')[1]
        if actType == "logout":
            self.sock.close()
if __name__ == '__main__':
    try:
        Client(host='localhost')
    except IndexError as e:
        print(e)
        print('Usage: python3 client.py Host Port')
    except NameError as e:
        print(e)
