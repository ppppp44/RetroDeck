from __future__ import annotations
import os, time, zipfile, threading
from pathlib import Path
from .database import Database, DEFAULT_SYSTEMS
from .catalog import CATALOG

EXCLUDES={'.git','node_modules','__pycache__'}
CATALOG_EXTENSIONS={ext for s in CATALOG for ext in s.extensions}
CATALOG_EXTENSIONS.update(ext for exts in DEFAULT_SYSTEMS.values() for ext in exts.split(','))
class ScanControl:
    def __init__(self): self.cancelled=threading.Event(); self.paused=threading.Event()
    def pause(self): self.paused.set()
    def resume(self): self.paused.clear()
    def cancel(self): self.cancelled.set()
    def wait(self):
        while self.paused.is_set() and not self.cancelled.is_set(): time.sleep(.05)
def system_for(path, folder_hint=''):
    ext=Path(path).suffix.lower(); hint=folder_hint.lower()
    for system, exts in DEFAULT_SYSTEMS.items():
        if ext in {x.strip() for x in exts.split(',')}: return system, False
    for s in CATALOG:
        if s.system_id in hint.replace(' ','_') or any(a.casefold() in hint for a in s.aliases): return s.name, True
    return 'Unknown', True

def scan_directory(db: Database, directory_id: int, root: str, cancel=None, control=None, progress=None):
    rootp=Path(root).expanduser(); started=time.time(); count=0; seen=set(); errors=[]
    if not rootp.is_dir(): db.mark_unavailable_under(rootp); return 0, f'Folder unavailable: {rootp}'
    try:
        for base, dirs, files in os.walk(rootp, followlinks=False):
            dirs[:]=[d for d in dirs if d not in EXCLUDES and not (Path(base)/d).is_symlink()]
            for fn in files:
                if control: control.wait()
                if (cancel and cancel.is_set()) or (control and control.cancelled.is_set()): return count,'Cancelled'
                path=Path(base)/fn
                try:
                    st=path.stat(); system, uncertain=system_for(path, str(path.parent))
                    if path.suffix.lower() not in CATALOG_EXTENSIONS: continue
                    if path.suffix.lower() in {'.zip','.7z'} and path.suffix.lower()=='.zip':
                        try:
                            members=[Path(n).suffix.lower() for n in zipfile.ZipFile(path).namelist() if not n.endswith('/')]
                            if not any(x in CATALOG_EXTENSIONS and x not in {'.zip','.7z'} for x in members): continue
                        except (OSError, zipfile.BadZipFile): uncertain=True
                    db.upsert_game({'title':path.stem,'filename':fn,'path':str(path.resolve()),'system':system,'extension':path.suffix.lower(),'size':st.st_size,'mtime':st.st_mtime,'available':1,'emulator':None,'uncertain':1 if uncertain else 0}); count+=1; seen.add(str(path.resolve()))
                    if progress: progress(count, str(path))
                except OSError as e: errors.append(str(e))
        db.mark_unavailable_under(rootp)
        if seen:
            q=','.join('?' for _ in seen); db.conn.execute(f'UPDATE games SET available=1 WHERE path IN ({q})',tuple(seen)); db.conn.commit()
        with db.conn: db.conn.execute('UPDATE game_directories SET last_scan=?,game_count=? WHERE id=?',(time.time(),count,directory_id))
        return count, '; '.join(errors[:3])
    except Exception as e: return count, str(e)
