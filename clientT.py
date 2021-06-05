import socket, sys
import os
import shutil
import time
import logging
from file import *
from datetime import datetime

from APIS.networkio import *
from Encryptions.hashmd5 import doHash
from Encryptions.caser import caesar


'''
    i.   I add some functions
            1.caesar cipher
            2.hash
            3.savingpath ex: send_file(self,file,savingpath)
    ii.  I also modify save_file as member of class NetAPI
    iii. Templfiles (from blocks) are stored in "../file/tempfie" by default
'''

logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

def client(host="127.0.0.1", port=7000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect( (host, port) )
    handle = NetAPI(sock)
    path ='/home/pi/Desktop/pi.pdf'
    handle.send_file(path)
    sock.close()
     
class NetAPI:
    FILE_TAG_SIZE       = 8
    FILE_END_TAG        = b'FILEEND0'
    FILE_NAME_TAG       = b'FILENAME'
    FILE_SIZE_TAG       = b'FILESIZE'
    FILE_CONTENT_TAG    = b'FILEDATA'
    FILE_ABORT_TAG      = b'FILEABRT'
    FILE_BLOCKS_TAG     = b'FILEBLKS'
    FILE_MODIFIED_TIME  = b'FILEMODI'
    FILE_HASH_TAG       = b'FILEHASH'
    FILE_PATH_TAG       = b'FILEPATH'

    #
    '''
    FILE_TAG_SIZE       = 8
    FILE_END_TAG        = caesar('FILEEND0',shift).encrypt().encode()
    FILE_NAME_TAG       = caesar("FILENAME",shift).encrypt().encode()
    FILE_SIZE_TAG       = caesar('FILESIZE',shift).encrypt().encode()
    FILE_CONTENT_TAG    = caesar("FILEDATA",shift).encrypt().encode()
    FILE_ABORT_TAG      = caesar('FILEABRT',shift).encrypt().encode()
    FILE_BLOCKS_TAG     = caesar("FILEBLKS",shift).encrypt().encode()
    FILE_MODIFIED_TIME  = caesar('FILEMODI',shift).encrypt().encode()
    FILE_TARGET_TAG     = caesar("TARGETER",shift).encrypt().encode()
    FILE_HASH_TAG       = caesar("FILEHASH",shift).encrypt().encode()
    FILE_PATH_TAG       = caesar('FILEPATH',shift).encrypt().encode()
    #FILE_TARGET_TAG     = caesar('RECVNAME',shift).encrypt().encode()
    #FILE_SENDER_TAG     = caesar('SENDNAME',shift).encrypt().encode()
    '''
    
    def __init__(self, iHandle=None, oHandle=None, filelocation='file/tempfile'):
        if not iHandle:
            iHandle     = b''
        if not oHandle:
            oHandle     = iHandle
        self.iHandle    = NetworkIO(iHandle)
        self.oHandle    = NetworkIO(oHandle)
        self.savePath   = filelocation
        '''len(block) + totalSize <= self.maxSize, 'Exceed Max File Size Limit'''
        self.maxSize    = 2147483647
        self.blockSize  = 4096          
    

    def send_tag(self, tag):   self.oHandle.write_raw(tag)
    def recv_tag(self): return self.iHandle.read_raw(self.FILE_TAG_SIZE)
    
    def send_data(self, data): self.oHandle.write(data) # convert data to bytes
    def recv_data(self): return self.iHandle.read()     # conver bytes to data 

    def send_name(self,s) : self.send_data(s)
    def recv_name(self) :
        path = self.recv_data()
        if isinstance(path, str): f'Invalid size type : {type(path)}'
        return path

    def send_path(self,savingpath): self.send_data(savingpath)
    def recv_path(self):
        savingpath = self.recv_data()
        if not isinstance(savingpath, str) : f'Invalid size type : {type(savingpath)}'
        return savingpath

    def send_size(self, n):  return self.send_data(n)
    def recv_size(self):
        size = self.recv_data()
        if not isinstance(size, int):f'Invalid size type : {type(size)}'
        return size
    
    def send_mtime(self,mtime): return self.send_data(mtime)
    def recv_mtime(self):
        mtime =self.recv_data()
        assert isinstance(mtime, float),f'Invalid size type : {type(mtime)}'
        return mtime
    
    def send_content(self, d):  return self.send_data(d)
    def recv_content(self):     return self.recv_data()
    
    def send_digest(self,md5): return self.send_data(md5)
    def recv_digest(self):     return self.recv_data()

    ''' Send File 
    | tag | name | tag | modified time | tag | filesize | tag | md5 |
    '''
    def send_file(self,path, savingpath="file/Public"):
        logging.info("[DEBUG]<<<<File Seding Progress Starts>>>>")
        md5 = doHash()
        digest = md5.hashmd5(path)
        fileModified = timeUpdate(path)
        mtime        = fileModified.getModitime()
        filename     = self.pathsplit(path)[-1]
        filesize     = os.path.getsize(path)
        filedata     = open(path, 'rb').read()
        try:
            self.send_tag(self.FILE_NAME_TAG) 
            self.send_name(filename)
            self.send_tag(self.FILE_MODIFIED_TIME)
            self.send_mtime(mtime)
            self.send_tag(self.FILE_SIZE_TAG)
            self.send_size(filesize)
            self.send_tag(self.FILE_HASH_TAG)
            self.send_digest(digest)
            self.send_tag(self.FILE_PATH_TAG)
            self.send_path(savingpath)
            
            '''if the transfering file is too big
               I cut it into blocks (sending it one by one)
               else we send it at one time
            '''
            if filesize > self.blockSize:    #filesize excess the upperbound
                self.send_tag(self.FILE_BLOCKS_TAG)
                self.send_blocks(path)
            else:
                self.send_tag(self.FILE_CONTENT_TAG)
                self.send_content(filedata)
            self.send_tag(self.FILE_END_TAG)
            return True
        except Exception as e:
            print(e.args)
            # send a message to inform receiver 
            self.send_tag(self.FILE_ABORT_TAG)
            return False
        logging.info("[DEBUG]<<<<File Sending Progress Ends>>>>")
   

    '''Using Tag to process receiving '''
    def recv_file(self):
        logging.info("[DEBUG]<<<<File Receiving Progress Starts>>>>")
        result = {}
        while True:
            tag = self.recv_tag()
            
            logging.debug(f'[DEBUG] filetag : {tag}')
            if not tag or tag in [self.FILE_END_TAG, self.FILE_ABORT_TAG]: break
            
            '''receiving the file in blocks or A complete file '''
            if tag == self.FILE_BLOCKS_TAG:
                tempfile = self.recv_blocks()
                logging.debug(f'[DEBUG] receiving tempfile: *{tempfile}*')
                result[tag] = tempfile
            else:
                #recve_data() -> nbyte to data 
                data = self.recv_data()
                #logging.debug(f'[DEBUG] Receiving data : {data} ')
                if not data: break 
                result[tag] = data
        logging.info("[DEBUG]<<<<File Receiving Progress Ends>>>>")
        self.result = result
        return self.result
       
    def send_blocks(self, fileName):
        '''sending is not rb => assertion : Invalid Type Of Block'''
        logging.info(f'[DEBUG] **SEND_BLOCKS Progress Starts**')
        fp        = open(fileName, 'rb')
        blockID   = 0 # to record each block's name 
        totalSize = 0 # to record each block's size
        with open(fileName,'rb') as fp:
            while True:
                # fp read a block size data
                block      = fp.read(self.blockSize)
                assert isinstance(blockID, int), f'invalid type of block id {blockID}'
                if not block : break
                blockID   += 1
                self.send_data(blockID)
                self.send_data(block)
                totalSize += len(block)
        
        #send_data(0) : end number
        self.send_data(0) 
        logging.info(f'[DEBUG] **SEND_BLOCKS Progress Ends**')
        return totalSize
        
    def recv_blocks(self):
        logging.info("[DEBUG]**RECV_BLOCKS Progress Starts**")
        totalSize   = 0
        lastBlockID = 0
        tempfilename = str(datetime.now().strftime('%m-%d_%X'))
        filename = os.path.abspath(os.path.join(self.savePath, tempfilename ))
        dirname  = os.path.dirname(filename)
        logging.debug(f'[DEBUG] directory path of temp {dirname}')
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(filename, 'wb') as fp:
            while True: #receiving block one by one
                # With order : | ID | Block size | FILE | BLOCKDATA |
                blockID = self.recv_data()
                logging.debug(f'[DEBUG] Receiving BlockID : {blockID}')
                assert isinstance(blockID, int), f'invalid type of block id {blockID}'
                if blockID == 0:
                    break
                assert (lastBlockID + 1 == blockID),f'block ID error last: {lastBlockID} current:{blockID}'
                lastBlockID = blockID
                
                block   = self.recv_data()
                logging.debug(f'[DEBUG] Receiving block*data*')
                assert isinstance(block,bytes),f'Invalid Type Of Block {type(block)}'
                logging.debug(f'[DEBUG] Length of Block : {len(block)}')
                assert len(block) + totalSize <= self.maxSize, 'Exceed Max File Size Limit'
                logging.info(f'[DEBUG] writing data into {filename} ')
                
                fp.write(block)
                logging.info(f'[DEBUG] writing data into {filename} successfully')
        logging.info("[DEBUG]**RECV_BLOCKS Progress Ends**")
        return filename

    def pathsplit(self,path):
        logging.debug(f'[DEBUG] PATHSPLIT progress Starts')
        result = []
        # Do recursively function 
        while True:
            head,tail = os.path.split(path)
            if tail:
                result.insert(0, tail)
                path = head
            else:
                head = head.strip('/:\\')
                if head: result.insert(0, head)                
                break
        logging.debug(f'After Spliting {result}')
        return result        

    '''using get() to get each element ..filename, modifedtime, filename,...filesize in {}'''
    def save_file(self,target):
        logging.info("[DEBUG]**save_file Porgress Starts**")

        filemtime=self.result.get(NetAPI.FILE_MODIFIED_TIME)
        logging.debug(f'[DEBUG] GET fileModifiedtime:{filemtime}')
        
        filename= self.result.get(NetAPI.FILE_NAME_TAG)
        logging.debug(f'[DEBUG] Get filename:{filename}')
        
        filesize= self.result.get(NetAPI.FILE_SIZE_TAG)
        logging.debug(f'[DEBUG] Get filesize: {filesize}')
        
        tempfile = self.result.get(NetAPI.FILE_BLOCKS_TAG)
        logging.debug(f'[DEBUG] Get tempfile: {tempfile}')
        
        content  = self.result.get(NetAPI.FILE_CONTENT_TAG)
        logging.debug(f'[DEBUG] Get Content of File {content}')
        
        savepath = self.result.get(NetAPI.FILE_PATH_TAG)
        logging.debug(f'[DEBUG] Get SAVINGPATH of File {savepath}')
        

        '''
            check for filename and filesize , content and tempfile
        '''        
        if not filename or not filesize:
            logging.debug(f'[DEBUG] check out your filename :{filename} and filesize : {filesize}')
            return False
        if not content and not tempfile:
            logging.debug(f'[DEBUG] Error for content {content} and tempfile {filesize}')
            return False
        else:
            fullname = os.path.join(target, filename)
            dirname  = os.path.dirname(fullname)            
            if not os.path.exists(dirname):
                os.makedirs(dirname)

            ''' 
            file content tag includes two information 
                the file you are saving is A complete file or the blocks
            '''
            # recv_cotent
            if content: 
                assert len(content)==filesize , 'Size Unmatches'
                with open(fullname, 'wb') as fp:
                    fp.write(content)
                os.utime(fullname,(filemtime,filemtime))
            
            # recv_block 
            else:
                try:
                    assert (os.path.getsize(tempfile) == filesize ), 'Size Unmatched'
                    shutil.move(tempfile, fullname)
                except AssertionError:
                    logging.info("[DEBUG]**Size Unmatched**")
        
        logging.info("[DEBUG]**save_file Porgress Ends**")
        return True
        
if __name__ == "__main__":
    client = client()