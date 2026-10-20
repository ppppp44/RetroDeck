from __future__ import annotations
import time
from .database import Database
from .process_adapters import adapter_for_platform, spawn

def build_command(emulator, game, core=None, extra=''):
    """Preview a platform-correct argv list without requiring files to exist."""
    return adapter_for_platform().command(emulator, game, core, extra, validate_paths=False)

def launch(db: Database, game, emulator, core=None, extra=''):
    started=time.time()
    try:
        proc,cmd=spawn(adapter_for_platform(), emulator, game, core, extra)
    except Exception as e:
        with db.conn:
            db.conn.execute('INSERT INTO game_launch_history(game_id,started,success,error) VALUES(?,?,0,?)',(game['id'],started,str(e)))
        raise
    with db.conn:
        db.conn.execute('UPDATE games SET last_played=?,launch_count=launch_count+1 WHERE id=?',(started,game['id']))
        db.conn.execute('INSERT INTO game_launch_history(game_id,started,success) VALUES(?,?,1)',(game['id'],started))
    return proc,cmd
