import sys
import hashlib

'''
Preventing file from being modified while tranfering
'''

class doHash:
    def __init__(self):
        self.buffsize = 4086
        self.md5 = hashlib.md5()
    def hashmd5(self,path):
        with open(path, 'rb') as f:
            while True:
                data = f.read(self.buffsize)
                if not data:
                    break
                self.md5.update(data)
        return self.md5.hexdigest()

