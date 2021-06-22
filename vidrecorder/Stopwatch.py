import time
import tkinter
from tkinter import Frame, Label, StringVar
from tkinter.constants import NO, X

class StopWatch(Frame):
    def __init__(self,parent=None, **kw):
        Frame.__init__(self,parent,kw)
        self._start = 0.0
        self.elapsedTime=0.0
        self.running=0
        self.timeStr = StringVar()
        self.makeWidgets()

    def _update(self):
        self.elapsedTime = time.time() - self._start
        self.setTime(self.elapsedTime)
        self._timer = self.after(50,self._update)

    def makeWidgets(self):
        l= Label(self,textvariable=self.timeStr)
        self.setTime(self.elapsedTime)
        l.pack(fill=X,expand=NO,pady=2,padx=2)

    def setTime(self,elap):
        hours = int((elap/60)/60)
        minutes = int(elap/60)
        seconds = int(elap-minutes*60.0)
        #hseconds = int((elap-minutes*60.0-seconds)*100)
        self.timeStr.set('%02d:%02d:%02d' % (hours,minutes,seconds))

    def Start(self):
        if not self.running:
            self._start = time.time() - self.elapsedTime
            self._update()
            self.running =1

    def Stop(self):
        if self.running:
            self.after_cancel(self._timer)
            self.elapsedTime=time.time() - self._start
            self.setTime(self.elapsedTime)
            self.running = 0

    def Reset(self):
        self._start = time.time()
        self.elapsedTime = 0.0
        self.setTime(self.elapsedTime)