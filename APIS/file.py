import datetime, time
import os

'''
    update file modified time
'''

class timeUpdate:
    def __init__ (self,filepath):
        self.filepath = filepath
        self.t = datetime.datetime.now()
        self.mtime = time.mktime(self.t.timetuple())
    def getModitime(self):
        return self.mtime
    def setModitime(self):
        return os.utime(self.filepath ,(self.mtime,self.mtime))
        