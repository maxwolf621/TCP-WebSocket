'''  
Implementation of Chain GUI interface using by mttkinter
'''
from mttkinter import mtTkinter as tk
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog
import threading
import logging
import os,sys
enCode = 'utf-8'

class GUI(threading.Thread):
    def __init__(self, client):
        super().__init__(daemon=False, target=self.run)
        self.font = ('Helvetica', 15)
        self.client = client
        self.userName = None
        self.mainWindow = None
        self.close = None
        
    def run(self):
        self.userName   = CreateName(self , self.font)
        self.mainWindow = ChatWindow(self , self.font)
        self.notifyClient(self.userName.user, 'login')
        if self.close == 1:
            logging.info('[DEBUG] CLOSING THE APPLICATION')
            self.close = 0 
        else:
            self.mainWindow.run()
    
    @staticmethod
    def alertMsgbox(message):
        try:
            messagebox.showinfo('Error', message)
        except RuntimeError as e:
            print(e.args)
    
    '''Class Client passes arguments to Class ChatWindow via Class GUI'''
    def updateUserslist(self, onlineUsers):
        #update list
        self.mainWindow.updateUsersList(onlineUsers)
    def updateFilesList(self, files):
        self.mainWindow.updateFilesList(files)
    def updatePrivateFilesList(self,files):
        self.mainWindow.updatePrivateFilesList(files)
    def displayMessage(self, message):
        self.mainWindow.displayMessage(message) 
    def displayPrivateMessage(self, message):
        self.mainWindow.displayPrivateMessage(message)
    def set_target(self, target):
        self.client.target = target
    
    '''pass information to class client via class Gui'''
    def login(self, login):
        self.client.notifyServer(login, 'login')
    def logout(self, logout):
        self.client.notifyServer(logout, 'logout')
    def notifyClient(self, message, action):
        #try:
        data = action + ";" + message
        data=  data.encode(enCode)
        self.client.notifyServer(data, action)
        #except TypeError as e:
        #    logging.debug('[WARNING] User Closes the CreateName Window')
        #    self.mainWindow.root.quit()
        #    self.close = 1
        #    self.mainWindow.root.destroy()
            
    ''' Class ChatWindow passes arguments to Class Client'''
    def uploadFile(self,filename,savingpath):
        logging.debug(f'[DEBUG] **UPLOAD FILE** Put Information :filename->{filename} and savingpath->{savingpath} into upServer')
        self.client.queueToUpSer.put((filename,savingpath))
        #call runUploadSerer() in the class client to send file to upServer
        self.client.runUploadSerer()
    def downloadFile(self,enMsg):
        logging.debug(f'[DEBUG] **DOWNLOAD FILE** Put Information :{enMsg} into DwServer')
        self.client.queueToDwSer.put(enMsg)
    def sendMsg(self, enMsg):
        logging.debug(f'[DEBUG] **SEND MESSAGE**  Put Message : {enMsg} into Chat Server)')
        self.client.queueSerChat.put(enMsg)

class Window(object):
    def __init__(self, title, font):
        self.root = tk.Tk()
        self.title = title
        self.root.title(title)
        self.font = font
        
class CreateName(Window):
    def __init__(self, gui, font):
        super().__init__("Create your NickName", font)
        self.gui = gui
        self.label = None
        self.entry = None
        self.button = None
        self.user = None
        self.displayWindow()
        self.run()
    def displayWindow(self):
        self.root.resizable(0,0)
        self.label = tk.Label(self.root, text='Enter your nickName',
                              width=20, font=self.font)
        self.label.pack(side=tk.LEFT, expand=tk.YES)
        #create name 
        self.entry = tk.Entry(self.root, width=20, font=self.font)
        self.entry.focus_set()
        self.entry.pack(side=tk.LEFT)
        self.entry.bind('<Return>', self.getLoginchatroom)
        #button
        self.button = tk.Button(self.root, text='Login', font=self.font)
        self.button.pack(side=tk.LEFT)
        self.button.bind('<Button-1>', self.getLoginchatroom)
    def run(self):
        try:
            self.root.mainloop()
            self.root.destroy()
        except:
            pass
    def getLoginchatroom(self, event=None):
        self.user = self.entry.get()
        assert self.user !=None, 'None'
        self.root.quit()
            
class ChatWindow(Window):
    def __init__(self, gui, font):
        super().__init__("chatter", font)
        self.font = font
        self.gui = gui
        self.lock = threading.RLock()
        self.user = self.gui.userName.user
        #
        self.messages_list = None
        self.usersList= None
        self.filesList = None
        self.entry = None
        self.sendButton = None
        self.exit_button = None
        self.file = ' '
        self.target = ''
        self.targetList=[]
        self.displayWindow()
    def displayWindow(self):
        '''------------------------------Window Size--------------------------'''
        self.root.geometry("550x500")
        self.root.resizable(0,0)
        '''---------------------------------Widget----------------------------'''
        # ScrolledText widget for displaying messages
        self.messages_list = scrolledtext.ScrolledText(self.root, wrap='word', font=self.font)
        self.messages_list.configure(state='disabled')
        # Listbox widget for displaying active users and selecting them
        self.usersList= tk.Listbox(self.root, selectmode=tk.SINGLE, font=self.font,exportselection=False)
        self.usersList.bind('<<ListboxSelect>>', self.selectUser)
        #listbox widget for displaying file stored in server dir                                                                                                                                                                                                                             
        self.filesList= tk.Listbox(self.root, selectmode=tk.SINGLE, font=self.font,exportselection=False)
        #self.filesList.bind('<<ListboxSelect>>', self.selectFile)
        #txtInput widget for typing messages in
        self.entry = tk.Text(self.root ,bg="lightgreen", width="10", height="1", font=("Arial", 12))
        self.entry.focus_set()
        self.entry.bind('<Return>', self.sendMessages)
        '''---------------------------------Button-----------------------------'''
        #Button widget for sending messages
        self.sendButton = tk.Button(self.root)
        self.img =tk.PhotoImage(file="png/send.png") 
        self.sendButton.config(image=self.img)
        self.sendButton.bind('<Button-1>', self.sendMessages)
        #Button widget for sending file
        self.upFile = tk.Button(self.root, text="Attach", font=30, width="18", height=3, bd=0, command=self.sendFile)
        self.upfileImg =tk.PhotoImage(file='png/upload.png') 
        self.upFile.config(image=self.upfileImg)
        #Button widget for update  
        self.update = tk.Button(self.root, text="Attach", font=30, width="18", height=3, bd=0, command=self.update)
        self.updateImg =tk.PhotoImage(file='png/update.png') 
        self.update.config(image=self.updateImg)
        #Button widget for download
        self.download = tk.Button(self.root, text="Attach", font=30, width="18", height=3, bd=0, command=self.selectFile)
        self.downloadImg =tk.PhotoImage(file='png/download.png') 
        self.download.config(image=self.downloadImg)
        '''--------------------------Locating the Widgets---------------------'''
        self.messages_list.place(x=6, y=40, height=352, width=370)
        self.entry.place(x=6, y=401, height=90, width=265)
        self.sendButton.place(x=285, y=401, height=90, width=90)
        self.usersList.place(x=400,y=40, height=200, width=150)
        self.filesList.place(x=400,y=250, height=200, width=150)
        self.upFile.place(x=435, y=455, height=32, width=32)
        self.download.place(x=400,y=455, height=32, width=32)
        self.update.place(x = 468, y=455 ,height = 32 ,width=32)
        '''--------------------------Protocol---------------------------------'''
        #Protocol for closing window using 'x' button
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)
        
    
    def run(self):
        self.root.mainloop()
        self.root.destroy()
    '''----------------- methods--------------'''
    def selectUser(self, event=None):
        '''
        Set as target currently selected login on login list
        '''
        self.target = self.usersList.get(self.usersList.curselection())
        self.gui.set_target(self.target)
        if self.target != 'all':
            logging.debug(f'[DEBUG] Pop-up the Private Window with {self.target}')
            if not self.target in self.targetList :
                self.targetList.append(self.target)
                self.openPrivateWindow(self.gui.mainWindow, self.target, self.user, self.gui, self.font)
            else :
                print(f'the chatwindow with {self.target} is already on')
    #
    def openPrivateWindow(self,root,target,user,gui,font):
        self.toplevel = privateWindow(root,target,user,gui,font) 
    #
    def displayPrivateMessage(self,message):
        if not self.target in self.targetList :
            self.targetList.append(self.target)
            self.openPrivateWindow(self.gui.mainWindow, self.target, self.user, self.gui, self.font)
        self.toplevel.displayPrivateMessage(message)
    #
    def updatePrivateFilesList(self,files):
        self.toplevel.updateFilesList(files)
    #
    def update(self):
        '''Listfile update'''
        self.gui.notifyClient(self.user, 'fileupdate')           
    #
    def updateUsersList(self, onlineUsers):
        '''Update listbox'''
        self.usersList.delete(0, tk.END)
        for user in onlineUsers:
            if user != self.user:
                self.usersList.insert(tk.END, user)
                self.usersList.itemconfig(tk.END, fg='orange')
        self.usersList.select_set(0)
        self.target = self.usersList.get(self.usersList.curselection())
    #
    def updateFilesList(self,files):
        '''Updata FilesList'''
        self.filesList.delete(0, tk.END)  
        for file in files:
            self.filesList.insert(tk.END,file)
            self.filesList.itemconfig(tk.END, fg='green')
        self.filesList.select_set(0)
        self.file = self.filesList.get(self.filesList.curselection())
    #
    def onClosing(self):
        '''To Confirm action of closing window  '''
        if messagebox.askokcancel("Quit", "Leaving??"):
            self.gui.notifyClient(self.user, 'logout')
            try:
                self.root.quit()
            except:
                pass         
    #
    def displayMessage(self, message):
        '''Display on Screen '''
        with self.lock:
            self.messages_list.configure(state='normal')
            self.messages_list.insert(tk.END, message)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
    #    
    def selectFile(self, event=None):
        '''select File to download'''
        filename = self.filesList.get(self.filesList.curselection())
        logging.debug(f'[DEBUG] Select the file **{filename}** from listbox')
        savingpath = filedialog.asksaveasfilename(title='Save File To', initialfile=filename)
        if savingpath:
            logging.debug(f'[DEBUG] Saving File to {savingpath}')
            savingpath = os.path.dirname(savingpath)
            message = f'request;{self.user};all;{filename};{savingpath}'
            self.gui.downloadFile(message.encode())
        else:
            pass        
    #    
    def sendFile(self):
        ''' Processing of uploading Files ''' 
        message = f'You Are Sending A File to Everyone \n'
        filename = filedialog.askopenfilename()
        if filename and self.target !=' ' :
            savingpath = f'file/Public'
            self.gui.uploadFile(filename,savingpath)
            logging.debug(f'[DEBUG] Sending File is Processing NOW')
            self.displayMessage(message)
    #
    def sendMessages(self, event=None):
        ''' Processing of sending Text '''
        text = self.entry.get(1.0, tk.END)
        if text.strip():
            message = f'broadcast;{self.user};all;{text[:-1]}'
            # put message into queue
            self.gui.sendMsg(message.encode(enCode))
            logging.debug(f'[DEBUG] User\'s message put into queue Successfully')
            self.entry.mark_set(tk.INSERT, 1.0) 
            self.entry.delete(1.0, tk.END) 
            self.entry.focus_set()
        with self.lock:
            self.messages_list.configure(state='normal')
            if text != '\n':
                self.messages_list.insert(tk.END, 'ME: ' + text)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
        return 'break'
    
class privateWindow(tk.Toplevel):
    def __init__(self,root,target,user,gui,font):
        tk.Toplevel.__init__(self)
        self.root = root
        self.title(f'User:{target}')
        self.gui = gui
        self.font = font
        self.user = user
        self.target = target
        self.messages_list = None
        self.filesList = None
        self.entry = None
        self.sendButton = None
        self.exit_button = None
        self.lock = threading.RLock()
        self.file = ' '
        self.target = target
        self.displayWindow()   
    def displayWindow(self):
        '''------------------------------Window Size--------------------------'''
        self.geometry("550x500")
        self.resizable(0,0)
        
        '''---------------------------------Widget----------------------------'''
        # ScrolledText widget for displaying messages
        self.messages_list = scrolledtext.ScrolledText(self, wrap='word', font=self.font)
        self.messages_list.configure(state='disabled')
        #listbox widget for displaying file stored in server dir
        self.filesList= tk.Listbox(self, selectmode=tk.SINGLE, font=self.font,exportselection=False)
        #self.filesList.bind('<<ListboxSelect>>', self.selectFile)
        #txtInput widget for typing messages in
        self.entry = tk.Text(self ,bg="lightgreen", width="10", height="1", font=("Arial", 12))
        self.entry.focus_set()
        self.entry.bind('<Return>', self.sendMessages)
        
        '''---------------------------------Button-----------------------------'''
        #Button widget for sending messages
        self.sendButton = tk.Button(self)
        self.img =tk.PhotoImage(file="png/send.png") 
        self.sendButton.config(image=self.img)
        self.sendButton.bind('<Button-1>', self.sendMessages)
        #Button widget for sending file
        self.upFile = tk.Button(self, text="Attach", font=30, width="18", height=3, bd=0, command=self.sendFile)
        self.upfileImg =tk.PhotoImage(file='png/upload.png') 
        self.upFile.config(image=self.upfileImg)
        #Button widget for update  
        self.update = tk.Button(self, text="Attach", font=30, width="18", height=3, bd=0, command=self.update)
        self.updateImg =tk.PhotoImage(file='png/update.png') 
        self.update.config(image=self.updateImg)
        #Button widget for download
        self.download = tk.Button(self, text="Attach", font=30, width="18", height=3, bd=0, command=self.selectFile)
        self.downloadImg =tk.PhotoImage(file='png/download.png') 
        self.download.config(image=self.downloadImg)
        
        '''--------------------------Locating the Widgets---------------------'''
        self.messages_list.place(x=6, y=40, height=352, width=370)
        self.entry.place(x=6, y=401, height=90, width=265)
        self.sendButton.place(x=285, y=401, height=90, width=90)
        self.filesList.place(x=400,y=40, height=410, width=130)
        self.upFile.place(x=435, y=455, height=32, width=32)
        self.download.place(x=400,y=455, height=32, width=32)
        self.update.place(x = 468, y=455 ,height = 32 ,width=32)
        '''--------------------------Protocol---------------------------------'''
        #Protocol for closing window using 'x' button
        self.protocol("WM_DELETE_WINDOW", self.onClosing)
    #
    def selectFile(self, event=None):
        '''select File to download'''
        filename = self.filesList.get(self.filesList.curselection())
        logging.debug(f'the file :{filename} from listbox')
        savingpath =filedialog.asksaveasfilename(title='Save File To', initialfile=filename)
        logging.debug(f'Save file to path :{savingpath}')
        if filename:
            msg = f'request;{self.target};{self.user};{filename};{savingpath}'
            self.gui.downloadFile(msg.encode()) 
    # 
    def update(self):
        ''' notify Server to update the filelistbox '''
        msg = f'privatefileUpdate;{self.user};{self.target}'
        self.gui.notifyClient(self.user, msg)           
    #
    def updateFilesList(self,files):
        '''Updata FilesList of GUI interface'''
        self.filesList.delete(0, tk.END)  
        for file in files:
            self.filesList.insert(tk.END,file)
            self.filesList.itemconfig(tk.END, fg='green')
        self.filesList.select_set(0)
        self.file = self.filesList.get(self.filesList.curselection())
    #
    def onClosing(self):
        '''Confirm action of closing window  '''
        if messagebox.askokcancel("Quit", "Leaving??"):
            try:
                self.destroy()
                self.root.targetList.remove(self.target)
                logging.debug('[DEBUG] remove element: {self.targer} in the targetList')
            except:
                pass
    #
    def displayPrivateMessage(self, message):
        '''Display on Screen '''
        with self.lock:
            self.messages_list.configure(state='normal')
            self.messages_list.insert(tk.END, message)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
    #
    def sendFile(self):
        ''' Processing of sending Files ''' 
        filename = filedialog.askopenfilename()
        if filename and self.target !=' ' :
            savingpath= f'file/{self.user}{self.target}'
            self.gui.uploadFile(filename,savingpath)
            logging.debug(f'[DEBUG] Sending File is Processing')
            self.displayPrivateMessage(f'sending file to {self.target}\n')
            text = '<- is sending file to you, please check out the listbox.'
            message = f'msg;{self.user};{self.target};{text[:-1]}'
            self.gui.sendMsg(message.encode(enCode))
    #
    def sendMessages(self, event=None):
        text = self.entry.get(1.0, tk.END)
        if text.strip():
            message = f'msg;{self.user};{self.target};{text[:-1]}'
            # put message into queue
            self.gui.sendMsg(message.encode(enCode))
            logging.debug(f'[DEBUG] User\'s message (Private Message) put into queue Successfully')
            self.entry.mark_set(tk.INSERT, 1.0)
            self.entry.delete(1.0, tk.END)
            self.entry.focus_set()
        with self.lock:
            self.messages_list.configure(state='normal')
            if text != '\n':
                msg = f'ME : {text}'
                self.messages_list.insert(tk.END, msg)
            self.messages_list.configure(state='disabled')
            self.messages_list.see(tk.END)
        return 'break'


    
    


