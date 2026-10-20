from __future__ import annotations
import glob, os, struct, threading
from PySide6.QtCore import QObject, Signal, QThread

class JoystickWorker(QThread):
    action=Signal(str)
    def __init__(self): super().__init__(); self.stop_event=threading.Event(); self.devices=[]
    def run(self):
        self.devices=glob.glob('/dev/input/js*')
        handles=[]
        try:
            for path in self.devices:
                try: handles.append(open(path,'rb',buffering=0))
                except OSError: pass
            while not self.stop_event.is_set() and handles:
                for h in list(handles):
                    try: data=h.read(8)
                    except OSError: handles.remove(h); continue
                    if len(data)!=8: continue
                    _,value,event_type,number=struct.unpack('IhBB',data); event_type &= 0x7f
                    if event_type==2 and number in (0,1) and abs(value)>16000:
                        self.action.emit({(0,-1):'left',(0,1):'right',(1,-1):'up',(1,1):'down'}[(number,1 if value>0 else -1)])
                    elif event_type==1 and value:
                        self.action.emit({0:'accept',1:'back',7:'menu',9:'next'}.get(number,'accept'))
        finally:
            for h in handles:
                try:h.close()
                except OSError:pass
    def stop(self): self.stop_event.set()

class ControllerBridge(QObject):
    action=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent); self.worker=JoystickWorker(); self.worker.action.connect(self.action); self.worker.start()
    def close(self): self.worker.stop(); self.worker.wait(500)
