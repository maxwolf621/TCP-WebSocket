'''
using simple caesar encode to \
    proetect the file from exposeing
'''
class caesar():
    def __init__(self, string , shift):
        self.string = string
        self.shift = shift
        self.len_s = len(self.string)
        self.wheellower= 'abcdefghijklmnopqrstuvwxyz'
        self.wheelupper= 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.wheeldigit= '0123456789'
        self.new_s =""
        self.old_s =""
    def encrypt(self):
        for n in range(self.len_s):
            #find the location of each character of self.string in wheel
            if self.string[n].isupper():
                index_c = self.wheelupper.find(self.string[n])
                new = self.wheelupper[(index_c + self.shift) % 26]
            elif self.string[n].islower():
                index_c = self.wheellower.find(self.string[n])
                new = self.wheellower[(index_c + self.shift) % 26]
            elif self.string[n].isdigit():
                index_c = self.wheeldigit.find(self.string[n])
                new = self.wheeldigit[(index_c + self.shift) % 10]
            #else:
            #     print('it\'s not valid Alpahbetics ')
            self.new_s += new

        return self.new_s
    def decrypt(self):
        for n in range(self.len_s):
            if self.string[n].isupper():
                index_c = self.wheelupper.find(self.string[n])
                new =self.wheelupper[ (index_c - self.shift) % 26]
            elif self.string[n].islower():
                index_c = self.wheellower.find(self.string[n])
                new = self.wheellower[(index_c - self.shift) % 26]
            elif self.string[n].isdigit():
                index_c = self.wheeldigit.find(self.string[n])
                new = self.wheeldigit[(index_c - self.shift) % 10]
            self.old_s += new
            #yield self.wheel[index_c - self.shift % 26]
        return self.old_s
    def process(self,do_encrypt = True):
        if do_encrypt:
            c = self.encrypt()
        else:
            c = self.decrypt()
        for i in range(self.len_s):
            print(next(c), end='')
        print()

def main():    
    encrypt = caesar("FILESIZe1088902",7).encrypt()
    print(encrypt)
    decrypt = caesar("MPSLZPGl8755679",7).decrypt()
    print(decrypt)
if __name__ == '__main__':
    main()
    

    

            
            


        
