import tkinter
import tkinter.filedialog as filedialog
from tkinter import messagebox
import os
import requests
import hashlib
import vlc
import platform
import threading
import datetime

class Timer(threading.Thread):
    def __init__(self, callback, tick):
        threading.Thread.__init__(self)
        self.callback = callback
        self.stopFlag = threading.Event()
        self.tick = tick
        self.iters = 0

    def run(self):
        while not self.stopFlag.wait(self.tick):
            self.iters += 1
            self.callback()

    def stop(self):
        self.stopFlag.set()

    def get(self):
        return self.iters

class syncPlay:
    def __init__(self, window):
        self.window = window
        self.window.title("syncPlay")
        
        #Menu Bar
        self.menubar = tkinter.Menu(self.window)
        self.window.config(menu = self.menubar)
        fileMenu = tkinter.Menu(self.menubar, tearoff=0)
        fileMenu.add_command(label="Open", underline=0, command=self.openFile)
        fileMenu.add_command(label="Exit", underline=1, command=_quit)
        self.menubar.add_cascade(label="File", menu=fileMenu)
        self.menubar.add_command(label="Server", underline=0, command=self.openServerPanel)
        
        #Video Panel
        self.player = None
        self.videoPanel = tkinter.Frame(self.window, bg='black')
        self.canvas = tkinter.Canvas(self.videoPanel, bg='black').pack(fill=tkinter.BOTH,expand=1)
        self.videoPanel.pack(fill=tkinter.BOTH,expand=1)
        
        #Status Bar
        self.statusBar = tkinter.Label(self.window, text="Idle", anchor=tkinter.W, relief=tkinter.SUNKEN, bd=1)
        self.statusBar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
        
        #Player Controls
        controlFrame = tkinter.Frame(self.window)
        self.timeLabel = tkinter.Label(controlFrame, text="-/-")
        self.playBtn = tkinter.Button(controlFrame, text="Play", command=self.playFunc, state='disabled')
        self.stopBtn = tkinter.Button(controlFrame, text="Stop", command=self.stopMedia, state='disabled')
        self.timeLabel.pack(side=tkinter.LEFT, padx=10)
        self.playBtn.pack(side=tkinter.LEFT)
        self.stopBtn.pack(side=tkinter.LEFT)
        
        self.volumeVar = tkinter.IntVar()
        self.volSlider = tkinter.Scale(controlFrame, showvalue=0, variable=self.volumeVar, command=self.setVolume, from_=0, to=125, orient=tkinter.HORIZONTAL, length=100)
        self.volSlider.set(100)
        self.volSlider.pack(side=tkinter.LEFT)
        
        self.goToTimeEntry = tkinter.Entry(controlFrame, state='disabled', width=6)
        self.goToTimeBtn = tkinter.Button(controlFrame, text="Go", command=self.goToTime, state='disabled')
        self.goToTimeEntry.pack(side=tkinter.LEFT)
        self.goToTimeBtn.pack(side=tkinter.LEFT)
        
        controlFrame.pack(side=tkinter.BOTTOM)
        
        #Player Time Seek
        seekFrame = tkinter.Frame(self.window)
        self.seekVar = tkinter.DoubleVar()
        self.timeSlider = tkinter.Scale(seekFrame, variable=self.seekVar, from_=0, to=1000, orient=tkinter.HORIZONTAL, length=500, state='normal')
        self.timeSlider.pack(side=tkinter.BOTTOM, fill=tkinter.X,expand=1)
        seekFrame.pack(side=tkinter.BOTTOM,fill=tkinter.X)
        
        # VLC Player Instance
        self.Instance = vlc.Instance()
        self.player = self.Instance.media_player_new()
        
        #Checksum, Filename, State Initialization
        self.checksum = ""
        self.filename = ""
        self.state = "stop"
        
        #Timer Thread
        timer = Timer(self.updatePlayback, 1.0)
        timer.start()
        
        self.syncServerState()
        
        self.window.update()
    
    def syncServerState(self):
        try:
            data = requests.post(url='http://adildsw.pythonanywhere.com/syncplay')
            data = data.json()
            fileNameServ = data[0]['filename']
            checksumServ = data[0]['checksum']
            stateServ = data[0]['state']
            timeServ = data[0]['time']
            
            self.stopBtn.configure(state='disabled')
            self.playBtn.configure(state='disabled')
            self.goToTimeBtn.configure(state='disabled')
            self.goToTimeEntry.configure(state='disabled')
            self.playBtn.configure(text='Play')
            
            if fileNameServ == "null":
                self.statusBar.configure(text="No file loaded in Server")
                self.state = 'stop'
            else:
                if self.filename == "":
                    self.statusBar.configure(text="Server: Please load '" + fileNameServ + "'")
                    self.state = 'stop'
                elif self.checksum != checksumServ:
                    self.statusBar.configure(text="ERROR: MD5 Checksum Mismatch")
                    self.state = 'stop'
                elif stateServ == "play":
                    self.statusBar.configure(text="Sync Error: Please pause server state or reset server")
                    self.state = 'stop'
                else:
                    self.stopBtn.configure(state='normal')
                    self.playBtn.configure(state='normal')
                    if stateServ == "pause":
                        self.state = 'pause'
                        self.player.pause()
                        self.player.set_time(int(timeServ) * 1000)
                    elif stateServ == "stop":
                        self.player.stop()
                    self.statusBar.configure(text="Synchronized with Server")
                    self.window.bind("<space>", self.playFunc)
                    #Creating a thread to monitor server state changes
                    self.watcherTimer = Timer(self.serverWatcher, 1.0)
                    self.watcherTimer.start()
        except:
            self.statusBar.configure(text="ERROR: Cannot establish connection to server")
            self.state = 'stop'
    
    def serverWatcher(self):
        try:
            data = requests.post(url='http://adildsw.pythonanywhere.com/syncplay')
            data = data.json()
            stateServ = data[0]['state']
            timeServ = data[0]['time']
                
            if self.state == 'pause' and stateServ == 'pause' and int(self.timeSlider.get()) == int(timeServ):
                return
            elif self.state == 'pause' and stateServ == 'pause' and int(self.timeSlider.get()) != int(timeServ):
                self.player.set_time(int(timeServ) * 1000)
                self.statusBar.configure(text="Server: Media is paused")
            elif self.state == stateServ:
                return
            else:
                if stateServ == 'pause':
                    self.state = 'pause'
                    self.player.pause()
                    self.player.set_time(int(timeServ) * 1000)
                    self.statusBar.configure(text="Server: Media is paused")
                    self.playBtn.configure(text='Play')
                    self.goToTimeBtn.configure(state='normal')
                    self.goToTimeEntry.configure(state='normal')
                elif stateServ == 'play':
                    self.state = 'play'
                    self.player.play()
                    self.statusBar.configure(text="Server: Media is playing")
                    self.playBtn.configure(text='Pause')
                    self.goToTimeBtn.configure(state='disabled')
                    self.goToTimeEntry.configure(state='disabled')
                elif stateServ == 'stop':
                    self.state = 'stop'
                    self.player.stop()
                    self.statusBar.configure(text="Server: Media is stopped")
                    self.playBtn.configure(text='Play')
                    self.goToTimeBtn.configure(state='disabled')
                    self.goToTimeEntry.configure(state='disabled')
        except:
            self.statusBar.configure(text="ERROR: Lost connection to server")
    
    def openFile(self):
        fullname = filedialog.askopenfilename(title = "Choose Your File",filetypes = (("MKV Files", "*.mkv"),("MP4 Files","*.mp4")))
        if os.path.isfile(fullname):
            dirname  = os.path.dirname(fullname)
            self.filename = os.path.basename(fullname)
            self.Media = self.Instance.media_new(str(os.path.join(dirname, self.filename)))
            self.player.set_media(self.Media)
            if platform.system() == 'Windows':
                self.player.set_hwnd(self.videoPanel.winfo_id())
            elif platform.system() == 'Darwin':
                self.player.set_nsobject(self.videoPanel.winfo_id())
            else:
                self.player.set_xwindow(self.videoPanel.winfo_id())
            self.checksum = _getHash(str(os.path.join(dirname, self.filename)))
            self.player.play()
            self.syncServerState()
            if self.state == 'stop':
                self.player.stop()
    
    def playFunc(self, evt=None):
        state = self.playBtn.config("text")[4]
        if state == 'Play':
            self.playMedia()
        elif state == 'Pause':
            self.pauseMedia()
    
    def playMedia(self):
        url = 'http://adildsw.pythonanywhere.com/syncplay/play'
        try:
            requests.post(url)
        except:
            self.statusBar.configure(text="ERROR: Cannot connect to server")
    
    def pauseMedia(self):
        pauseTime = int(self.timeSlider.get())
        params = {'time': pauseTime}
        url = 'http://adildsw.pythonanywhere.com/syncplay/pause'
        try:
            requests.get(url, params=params)
        except:
            self.statusBar.configure(text="ERROR: Cannot connect to server")
            
    def stopMedia(self):
        url = 'http://adildsw.pythonanywhere.com/syncplay/stop'
        try:
            requests.get(url)
        except:
            self.statusBar.configure(text="ERROR: Cannot connect to server")
    
    def setVolume(self, evt):
        if self.player == None:
            return
        volume = self.volumeVar.get()
        if volume > 125:
            volume = 125
        if self.player.audio_set_volume(volume) == -1:
            messagebox.showerror("Error", "Failed to set volume")
    
    def updatePlayback(self):
        if self.player == None:
            return
        #Obtaining media length in seconds and reconfiguring the length of the timeSlider
        totalTime = self.player.get_length()
        if totalTime != -1:
            totalTime = totalTime * 0.001
            self.timeSlider.config(to=totalTime)
        else:
            self.timeSlider.config(to=1000)
        #Setting timeSlider value
        currentTime = self.player.get_time()
        if currentTime == -1:
            currentTime = 0
        currentTime = currentTime * 0.001
        self.timeSlider.set(currentTime)
        
        #Updating Time Label
        if totalTime == -1 or currentTime == -1:
            self.timeLabel.configure(text="-/-")
        else:
            currentShowTime = str(datetime.timedelta(seconds=currentTime)).split(".")[0]
            totalShowTime = str(datetime.timedelta(seconds=totalTime)).split(".")[0]
            self.timeLabel.configure(text=currentShowTime + "/" + totalShowTime)
    
    def goToTime(self):
        if self.player == None:
            return
        destMilli = self.goToTimeEntry.get()
        totalMilli = self.player.get_length()
        if destMilli.isdigit() == False:
            messagebox.showerror("Error", "Please input a valid second")
        elif (int(destMilli)*1000) > int(totalMilli):
            messagebox.showerror("Error", "Target time greater than total media time")
        else:
            params = {'time': int(destMilli)}
            url = 'http://adildsw.pythonanywhere.com/syncplay/pause'
            try:
                requests.get(url, params=params)
                self.statusBar.configure(text="Server: Media is paused")
            except:
                self.statusBar.configure(text="ERROR: Cannot connect to server")
            self.player.set_time(int(destMilli)*1000)
        
    def quitPlayer(self):
        self.window.quit()
        self.window.destroy()
        os._exit(1)
        
    def openServerPanel(self):
        syncPlayServer()

class syncPlayServer:
    def __init__(self):
        self.window = tkinter.Tk()
        self.window.title("syncPlay Server Panel")
        
        self.fileNameLabel = tkinter.Label(self.window, text="Filename: ")
        self.fileNameLbl = tkinter.Label(self.window, text="")
        
        self.checksumLabel = tkinter.Label(self.window, text="MD5 Checksum: ")
        self.checksumLbl= tkinter.Label(self.window, text="")
        
        self.stateLabel = tkinter.Label(self.window, text="State: ")
        self.stateLbl = tkinter.Label(self.window, text="")
        
        self.timeLabel = tkinter.Label(self.window, text="Time: ")
        self.timeLbl = tkinter.Label(self.window, text="")
        
        self.resetBtn = tkinter.Button(self.window, command=self.resetServer, text="Reset Server")
        self.loadBtn = tkinter.Button(self.window, command=self.loadToServer, text="Load to Server")
        
        self.fileNameLabel.grid(row=0, column=0, sticky='w', pady=5)
        self.fileNameLbl.grid(row=0, column=1, sticky='w', pady=5)
        self.checksumLabel.grid(row=1, column=0, sticky='w', pady=5)
        self.checksumLbl.grid(row=1, column=1, sticky='w', pady=5)
        self.stateLabel.grid(row=2, column=0, sticky='w', pady=5)
        self.stateLbl.grid(row=2, column=1, sticky='w', pady=5)
        self.timeLabel.grid(row=3, column=0, sticky='w', pady=5)
        self.timeLbl.grid(row=3, column=1, sticky='w', pady=5)
        self.resetBtn.grid(row=4, column=0, sticky='w')
        self.loadBtn.grid(row=4, column=1, sticky='w')
        
        self.readFromServer()
        
        self.window.resizable(0,0)
        
        self.window.mainloop()
    
    def readFromServer(self):
        try:
            data = requests.post(url='http://adildsw.pythonanywhere.com/syncplay')
            data = data.json()
            self.fileNameLbl.configure(text=data[0]['filename'])
            self.checksumLbl.configure(text=data[0]['checksum'])
            self.stateLbl.configure(text=data[0]['state'])
            self.timeLbl.configure(text=data[0]['time'])
        except:
            self.fileNameLbl.configure(text="")
            self.checksumLbl.configure(text="")
            self.stateLbl.configure(text="")
            self.timeLbl.configure(text="")
            messagebox.showerror("Error", "Cannot establish connection to server")
    
    def resetServer(self):
        try:
            requests.post(url='http://adildsw.pythonanywhere.com/syncplay/reset')
            messagebox.showinfo("Success", "Server Reset Successful")
        except:
            messagebox.showerror("Error", "Could not reset server")
        finally:
            self.readFromServer()
    
    def loadToServer(self):
        fullname = filedialog.askopenfilename(title = "Choose Your File",filetypes = (("MKV Files", "*.mkv"),("MP4 Files","*.mp4")))
        if os.path.isfile(fullname):
            dirname  = os.path.dirname(fullname)
            filename = os.path.basename(fullname)
            checksum = _getHash(str(os.path.join(dirname, filename)))
            try:
                params = {"filename": filename, "checksum": checksum, "state": "pause", "time": 0}
                requests.get(url='http://adildsw.pythonanywhere.com/syncplay/load', params=params)
                messagebox.showinfo("Success", "Info Loaded to Server Successfully")
            except:
                messagebox.showerror("Error", "Could not load to server")
            finally:
                self.readFromServer()
        
def _getSyncPlayWindow():
    if not hasattr(_getSyncPlayWindow, "window"):
        _getSyncPlayWindow.window= tkinter.Tk()
    return _getSyncPlayWindow.window
    
def _getHash(filepath, blocksize=2**20):
    fileSize = str(os.path.getsize(filepath))
    return hashlib.md5(fileSize.encode()).hexdigest()

def _getHashOriginal(filepath, blocksize=2**20):
    m = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()
    
def _quit():
    MsgBox = messagebox.askquestion("Exit", "Are you sure?")
    if MsgBox == 'yes':
        window = _getSyncPlayWindow()
        window.quit()
        window.destroy()
        os._exit(1)
    
if __name__ == "__main__":  
    window = _getSyncPlayWindow()
    window.protocol("WM_DELETE_WINDOW", _quit)
    syncPlay(window)
    window.mainloop()