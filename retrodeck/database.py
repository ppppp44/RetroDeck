from __future__ import annotations
import sqlite3, time, os
from pathlib import Path
from typing import Any

SCHEMA = '''
CREATE TABLE IF NOT EXISTS systems (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, extensions TEXT NOT NULL DEFAULT '', emulator TEXT, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS emulator_definitions (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, executable TEXT NOT NULL DEFAULT '', default_args TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'not tested', version TEXT NOT NULL DEFAULT '', working_directory TEXT NOT NULL DEFAULT '', launch_method TEXT NOT NULL DEFAULT 'auto');
CREATE TABLE IF NOT EXISTS game_directories (id INTEGER PRIMARY KEY, system TEXT NOT NULL, path TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1, priority INTEGER NOT NULL DEFAULT 0, last_scan REAL, game_count INTEGER NOT NULL DEFAULT 0, UNIQUE(system,path));
CREATE TABLE IF NOT EXISTS games (id INTEGER PRIMARY KEY, title TEXT NOT NULL, filename TEXT NOT NULL, path TEXT UNIQUE NOT NULL, system TEXT NOT NULL, extension TEXT NOT NULL, size INTEGER NOT NULL DEFAULT 0, mtime REAL NOT NULL DEFAULT 0, available INTEGER NOT NULL DEFAULT 1, emulator TEXT, core_path TEXT, favorite INTEGER NOT NULL DEFAULT 0, last_played REAL, launch_count INTEGER NOT NULL DEFAULT 0, uncertain INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS retroarch_cores (id INTEGER PRIMARY KEY, name TEXT NOT NULL, library_path TEXT UNIQUE NOT NULL, extensions TEXT NOT NULL DEFAULT '', systems TEXT NOT NULL DEFAULT '', enabled INTEGER NOT NULL DEFAULT 1, args TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS directory_scan_history (id INTEGER PRIMARY KEY, directory_id INTEGER NOT NULL, started REAL NOT NULL, finished REAL, found INTEGER DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS game_launch_history (id INTEGER PRIMARY KEY, game_id INTEGER, started REAL NOT NULL, success INTEGER NOT NULL DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS application_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS system_catalog (system_id TEXT PRIMARY KEY, name TEXT NOT NULL, manufacturer TEXT NOT NULL, category TEXT NOT NULL, era TEXT NOT NULL, aliases TEXT NOT NULL DEFAULT '', extensions TEXT NOT NULL DEFAULT '', core_hints TEXT NOT NULL DEFAULT '', verified INTEGER NOT NULL DEFAULT 1, notes TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS enabled_systems (system_id TEXT PRIMARY KEY, preferred_core_id INTEGER, enabled INTEGER NOT NULL DEFAULT 1, favorite INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS core_metadata (library_path TEXT PRIMARY KEY, display_name TEXT NOT NULL, version TEXT NOT NULL DEFAULT '', systems TEXT NOT NULL DEFAULT '', extensions TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'available', discovered_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS system_core_mappings (system_id TEXT NOT NULL, library_path TEXT NOT NULL, preferred INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(system_id, library_path));
CREATE TABLE IF NOT EXISTS setup_systems (system_id TEXT PRIMARY KEY, emulator_mode TEXT NOT NULL DEFAULT 'later', emulator_path TEXT NOT NULL DEFAULT '', core_path TEXT NOT NULL DEFAULT '', validation_status TEXT NOT NULL DEFAULT 'needs setup', updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS setup_directories (id INTEGER PRIMARY KEY, system_id TEXT NOT NULL, path TEXT NOT NULL, UNIQUE(system_id,path));
CREATE INDEX IF NOT EXISTS idx_games_title ON games(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_games_system ON games(system);
CREATE INDEX IF NOT EXISTS idx_games_available ON games(available);
'''

DEFAULT_EMULATORS = {
    'Cemu': '/data/Cemu-2.6-x86_64.AppImage',
    'Dolphin': '/data/Dolphin_Emulator-2606a-anylinux-x86_64.AppImage',
    'PCSX2': '/data/pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage',
    'RetroArch': '/data/RetroArch/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage',
    'RPCS3': '',
    'Ryujinx': '',
}
if os.name == 'nt':
    DEFAULT_EMULATORS = {name:'' for name in ('Cemu','Dolphin','RPCS3','Ryujinx','RetroArch')}
DEFAULT_SYSTEMS = {
    'Wii U': '.wua,.wud,. wux,.rpx'.replace(' ', ''), 'GameCube': '.iso,.rvz,.gcm,.ciso',
    'Wii': '.iso,.rvz,.wbfs,.wia,.gcz', 'PS2': '.iso,.chd,.cso,.bin,.cue',
    'NES': '.nes,.zip', 'SNES': '.sfc,.smc,.fig,.zip', 'Game Boy': '.gb,.gbc,.zip',
    'Game Boy Advance': '.gba,.zip', 'Genesis': '.md,.gen,.smd,.bin,.zip', 'PS1': '.bin,.cue,.chd,.pbp,.iso'
}
SCHEMA_VERSION=4

class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser(); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False); self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON'); self.migrate(); self.seed()
    def migrate(self):
        with self.conn:
            self.conn.executescript(SCHEMA)
            # Older RetroDeck releases used CREATE IF NOT EXISTS only. Keep that
            # behavior, but also repair databases from partial/early builds.
            repairs={'games':['uncertain INTEGER NOT NULL DEFAULT 0'], 'emulator_definitions':['status TEXT NOT NULL DEFAULT \'not tested\'','version TEXT NOT NULL DEFAULT \'\'','working_directory TEXT NOT NULL DEFAULT \'\'','launch_method TEXT NOT NULL DEFAULT \'auto\''], 'game_directories':['priority INTEGER NOT NULL DEFAULT 0','last_scan REAL','game_count INTEGER NOT NULL DEFAULT 0']}
            for table,columns in repairs.items():
                existing={row[1] for row in self.conn.execute(f'PRAGMA table_info({table})')}
                for definition in columns:
                    name=definition.split()[0]
                    if name not in existing: self.conn.execute(f'ALTER TABLE {table} ADD COLUMN {definition}')
            self.conn.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
    def seed(self):
        with self.conn:
            for name, exe in DEFAULT_EMULATORS.items(): self.conn.execute('INSERT OR IGNORE INTO emulator_definitions(name,executable) VALUES(?,?)',(name,exe))
            for name, ext in DEFAULT_SYSTEMS.items(): self.conn.execute('INSERT OR IGNORE INTO systems(name,extensions) VALUES(?,?)',(name,ext))
            from .catalog import CATALOG
            now=time.time()
            for s in CATALOG:
                self.conn.execute('''INSERT INTO system_catalog(system_id,name,manufacturer,category,era,aliases,extensions,core_hints,verified,notes) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(system_id) DO UPDATE SET name=excluded.name,manufacturer=excluded.manufacturer,category=excluded.category,era=excluded.era,aliases=excluded.aliases,extensions=excluded.extensions,core_hints=excluded.core_hints,verified=excluded.verified,notes=excluded.notes''', (s.system_id,s.name,s.manufacturer,s.category,s.era,','.join(s.aliases),','.join(s.extensions),','.join(s.core_hints),int(s.verified),s.notes))
    def setting(self,key,default=''):
        r=self.conn.execute('SELECT value FROM application_settings WHERE key=?',(key,)).fetchone(); return r['value'] if r else default
    def set_setting(self,key,value):
        with self.conn: self.conn.execute('INSERT INTO application_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value)))
    def list_games(self, search='', system='', availability='all', favorite=False, limit=1000):
        q='SELECT * FROM games WHERE 1=1'; p=[]
        if search: q+=' AND title LIKE ?'; p.append('%'+search+'%')
        if system: q+=' AND system=?'; p.append(system)
        if availability!='all': q+=' AND available=?'; p.append(1 if availability=='available' else 0)
        if favorite: q+=' AND favorite=1'
        q+=' ORDER BY title COLLATE NOCASE LIMIT ?'; p.append(limit)
        return self.conn.execute(q,p).fetchall()
    def upsert_game(self, data):
        cols='title,filename,path,system,extension,size,mtime,available,emulator,uncertain'; vals=[data.get(c) for c in cols.split(',')]
        with self.conn: self.conn.execute(f'''INSERT INTO games({cols}) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET title=excluded.title,filename=excluded.filename,system=excluded.system,extension=excluded.extension,size=excluded.size,mtime=excluded.mtime,available=excluded.available,uncertain=excluded.uncertain''',vals)
    def mark_unavailable_under(self, root):
        with self.conn: self.conn.execute('UPDATE games SET available=0 WHERE path LIKE ?', (str(Path(root).expanduser()).rstrip('/')+'/%',))
    def close(self): self.conn.close()
