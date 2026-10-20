from __future__ import annotations
import shutil, sqlite3, time
from pathlib import Path
from .database import Database

def backup_database(db: Database, destination: str | Path) -> Path:
    dest=Path(destination).expanduser(); dest.parent.mkdir(parents=True,exist_ok=True)
    db.conn.commit();
    with sqlite3.connect(dest) as target: db.conn.backup(target)
    return dest

def restore_database(db: Database, source: str | Path) -> Path:
    src=Path(source).expanduser()
    if not src.is_file(): raise FileNotFoundError(src)
    # Validate before replacing anything; the caller should close/reopen after restore.
    with sqlite3.connect(src) as check:
        check.execute('SELECT name FROM sqlite_master LIMIT 1').fetchall()
    backup=Path(str(db.path)+f'.before-restore-{int(time.time())}.bak')
    db.conn.commit(); shutil.copy2(db.path,backup)
    db.close(); shutil.copy2(src,db.path)
    return backup
