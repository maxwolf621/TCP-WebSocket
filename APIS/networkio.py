import socket, sys
import os
import shutil
import logging

#define ....
SIZE = 1 # header size 
ENcode = 'UTF-8'

logging.basicConfig(level=logging.DEBUG,format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")

import socket, struct
class NetworkIO:
    def __init__(self, sock):
        self.handle = sock
    # Encapsulate nbyte_to_data(),data_to_nbyte
    def read_handle(self, n):
        try:
            return self.handle.recv(n)   
        except BlockingIOError as e:
            print(e.args)
    def write_handle(self, d):
        return self.handle.send(d) 
    def read_raw(self, n):
        return self.read_handle(n)          
    def write_raw(self, d):
        return self.write_handle(d)         
    def read(self):
        return self.nbyte_to_data()
    def write(self, d):
        byte_data = self.data_to_nbyte(d)
        self.write_raw(byte_data)
    def close_handle(self):
        return self.handle.close()
 
    def data_to_nbyte(self, n):   
        ''' using isinstance to check the sending file dataType'''
        logging.info(f"[SHOW] data to nbyte {n}")
        try:
            if isinstance(n, int):      # type(n) == int
                if n < (1<<8):          # btw 0~255
                    tag = 'B'
                elif n < (1<<16):       # btw 256~65535
                    tag = 'H'
                elif n < (1<<32):       # btw 65536~4294967295
                    tag = 'L'
                else:                   # btw 4294967296~
                    tag = 'Q'
                result = tag.encode(ENcode) + struct.pack('!' + tag, n)
                logging.info(f'[SHOW] RETURN A PACK {result}')
                return result
            elif isinstance(n, float):
                tag = 'd'
                result = tag.encode(ENcode) + struct.pack('!'+ tag, n)
                logging.info(f'[SHOW] RETURN A PACK {result}')
                return result
            elif isinstance(n, bytes):
                tag = 's'
                result = tag.encode(ENcode) + self.data_to_nbyte(len(n)) + n
                logging.info(f'[SHOW] RETURN A PACK {result}')
                return result
            elif isinstance(n, str):
                n = n.encode(ENcode).strip()
                tag = 'c'
                result = tag.encode(ENcode) + self.data_to_nbyte(len(n)) + n
                logging.info(f'[SHOW] RETURN A PACK {result}')
                return result
            else:
                raise TypeError(f'Invalide Type {tag}')
        except UnicodeDecodeError as e:
            logging.info(f"[ERROR]{e}")

    def nbyte_to_data(self):
        # Tag Type 
        size_info = { 'B':1, 'H':2, 'L':4, 'Q':8, 'd':8 }
        # read 1 byte
        btag = self.read_raw(SIZE)       
        if not btag:  
            return None
        try:
            tag = btag.decode(ENcode)
        except UnicodeDecodeError :
            tag = btag.decode("ISO-8859-1")
            logging.info(tag)
        # According B, H, L, Q, F
        if tag in size_info:  
            size    = size_info[tag]
            # recv_size_info : 1, 2, 4, 8, 8 bytes
            bnum    = self.read_raw(size)
            result  = struct.unpack('!' + tag, bnum)[0] 
        elif tag in ['s','c']:
            size    = self.nbyte_to_data() 
            if size >= 65536:
                raise ValueError('length too long: ' + str(size))
            bstr    = self.read_raw(size) 
            result  = bstr if tag == 's' else bstr.decode(ENcode)
        else:
            result = self.read()
        return result




