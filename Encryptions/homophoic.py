''' homophonicSub '''
''' Concept : each character or number with various rational nums '''

import random
#import os <wihtout Cipher_Array them using split to get the array> 
from collections import defaultdict  

class HomophonicSub:
    def __init__(self,p_text):
        #initilize plain and cipher text
        self.p_text = p_text
        #for encrypt
        self.c_arr = []
        self.table = defaultdict(list)
        self.check_list= []
        self.record ={}
        self.c_string =""
    def set_num(self):
        return round(random.uniform(0,len(self.p_text)),1)
    def set_key(self):
        for i in self.p_text:
            num = self.set_num()
            self.check_list.append(num)
            #duplicate checker
            while (len(self.check_list) != len(set(self.check_list))):
                for n in range(len(self.check_list)):
                    num = self.set_num() 
                    self.check_list[n] = num
            self.table[i].append(num)
    def encrypt(self):
        self.set_key()
        self.record = {i : 0 for i in self.p_text}
        for c in self.p_text:            
            self.c_arr.append(self.table[c][self.record[c]])
            self.record[c] +=1
        for i in self.c_arr:
            self.c_string += str(i)
        return self.c_string
    def decrypt(self):
        p_text = ""
        for i in range(len(self.c_arr)):
            # To compare list[i] with each_key in our talbe
            for key,values in self.table.items():
                for value in values:
                    if self.c_arr[i] == value :
                        p_text += key
        return p_text
                
        
def main():
    a = HomophonicSub("FILEEND0")
    b=a.encrypt()
    print(b)
    c=a.decrypt()
    print(c)
if __name__ == "__main__":
    main()
    