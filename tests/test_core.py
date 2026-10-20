import os, tempfile, unittest
import zipfile
from pathlib import Path
from retrodeck.database import Database
from retrodeck.scanner import scan_directory
from retrodeck.launcher import build_command
from retrodeck.catalog import CATALOG, search_catalog
from retrodeck.core_discovery import discover_cores, core_matches
from retrodeck.discovery import mounted_volumes, likely_roots
from retrodeck.backup import backup_database, restore_database
from retrodeck.scanner import ScanControl
from retrodeck.setup_wizard import SetupWizard
from retrodeck.controller import ControllerBridge
from retrodeck.process_adapters import WindowsProcessAdapter

class CoreTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.db=Database(Path(self.tmp.name)/'db.sqlite3')
    def tearDown(self): self.db.close(); self.tmp.cleanup()
    def test_migration_and_defaults(self):
        self.assertTrue((Path(self.tmp.name)/'db.sqlite3').exists()); self.assertIsNotNone(self.db.conn.execute("select * from emulator_definitions where name='PCSX2'").fetchone())
    def test_multiple_roots_recursive_and_incremental(self):
        a=Path(self.tmp.name)/'A'; b=Path(self.tmp.name)/'B'/'Nested'; b.mkdir(parents=True); a.mkdir(); (a/'one.nes').write_text('x'); (b/'two.sfc').write_text('x')
        with self.db.conn:
            self.db.conn.execute("insert into game_directories(system,path) values('NES',?)",(str(a),)); aid=self.db.conn.execute('select last_insert_rowid()').fetchone()[0]
            self.db.conn.execute("insert into game_directories(system,path) values('SNES',?)",(str(b),)); bid=self.db.conn.execute('select last_insert_rowid()').fetchone()[0]
        self.assertEqual(scan_directory(self.db,aid,str(a))[0],1); self.assertEqual(scan_directory(self.db,bid,str(Path(self.tmp.name)/'B'))[0],1)
        self.assertEqual(self.db.conn.execute('select count(*) from games').fetchone()[0],2)
    def test_duplicate_path_and_missing_mount(self):
        a=Path(self.tmp.name)/'A'; a.mkdir(); f=a/'x.nes'; f.write_text('x')
        with self.db.conn:self.db.conn.execute("insert into game_directories(system,path) values('NES',?)",(str(a),)); did=self.db.conn.execute('select last_insert_rowid()').fetchone()[0]
        scan_directory(self.db,did,str(a)); scan_directory(self.db,did,str(a)); self.assertEqual(self.db.conn.execute('select count(*) from games').fetchone()[0],1)
        f.unlink(); scan_directory(self.db,did,str(a)); self.assertEqual(self.db.conn.execute('select available from games').fetchone()[0],0)
    def test_safe_commands_and_spaces(self):
        em={'name':'PCSX2','executable':'/tmp/a path.AppImage'}; game={'path':'/tmp/game (EU).chd'}
        self.assertEqual(build_command(em,game),['/tmp/a path.AppImage','--','/tmp/game (EU).chd'])
        ra=build_command({'name':'RetroArch','executable':'retroarch'},game,'/cores/snes_libretro.so'); self.assertIn('-L',ra)
    def test_windows_adapter_preserves_spaces_and_args(self):
        command=WindowsProcessAdapter().command({'name':'RPCS3','executable':r'C:\Emulators\RPCS3\rpcs3.exe','default_args':'--no-gui','working_directory':r'C:\Emulators\RPCS3'}, {'path':r'C:\My Games\PS3 Title\EBOOT.BIN'}, validate_paths=False)
        self.assertEqual(command[0],r'C:\Emulators\RPCS3\rpcs3.exe'); self.assertEqual(command[1],r'C:\My Games\PS3 Title\EBOOT.BIN'); self.assertEqual(command[2], '--no-gui')
    def test_universal_catalog_and_search(self):
        self.assertGreaterEqual(len(CATALOG),100)
        self.assertEqual(len({s.system_id for s in CATALOG}),len(CATALOG))
        self.assertTrue(any(s.system_id=='n64' for s in search_catalog('Nintendo 64')))
        self.assertTrue(self.db.conn.execute('select count(*) from system_catalog').fetchone()[0]>=100)
    def test_zip_rom_is_scanned_without_extracting(self):
        root=Path(self.tmp.name)/'ROMs'; root.mkdir(); z=root/'game.zip'
        with zipfile.ZipFile(z,'w') as archive: archive.writestr('game.nes',b'rom')
        with self.db.conn:self.db.conn.execute("insert into game_directories(system,path) values('NES',?)",(str(root),)); did=self.db.conn.execute('select last_insert_rowid()').fetchone()[0]
        self.assertEqual(scan_directory(self.db,did,str(root))[0],1); self.assertTrue(z.exists())
    def test_core_discovery_from_configured_directory(self):
        core_dir=Path(self.tmp.name)/'cores'; core_dir.mkdir(); (core_dir/'nestopia_libretro.so').write_bytes(b'ELF'); (core_dir/'nestopia_libretro.info').write_text('display_name = "Nestopia"\nsupported_extensions = "nes|fds"\n')
        old=__import__('retrodeck.core_discovery',fromlist=['DEFAULT_CORE_DIRS']).DEFAULT_CORE_DIRS[:]
        mod=__import__('retrodeck.core_discovery',fromlist=['DEFAULT_CORE_DIRS']); mod.DEFAULT_CORE_DIRS[:]=[core_dir]
        try:
            found=discover_cores(''); self.assertEqual(found[0]['name'],'Nestopia'); self.assertTrue(core_matches(next(s for s in CATALOG if s.system_id=='nes'),found[0]))
        finally: mod.DEFAULT_CORE_DIRS[:]=old
    def test_scan_control_pause_resume_cancel(self):
        control=ScanControl(); control.pause(); self.assertTrue(control.paused.is_set()); control.resume(); self.assertFalse(control.paused.is_set()); control.cancel(); self.assertTrue(control.cancelled.is_set())
    def test_backup_restore_preserves_database(self):
        self.db.set_setting('accent','violet'); target=Path(self.tmp.name)/'backup.sqlite3'; backup_database(self.db,target); self.db.set_setting('accent','cyan'); safety=restore_database(self.db,target); self.assertTrue(safety.exists()); restored=Database(self.db.path); self.assertEqual(restored.setting('accent'),'violet'); restored.close()
    def test_mount_discovery_is_bounded(self):
        volumes=mounted_volumes(); self.assertIsInstance(volumes,list); self.assertTrue(all(v['path'] not in ('/proc','/sys','/dev','/run','/tmp') for v in volumes)); self.assertIsInstance(likely_roots(volumes),list)
    def test_setup_tables_support_selected_systems_and_multiple_paths(self):
        self.assertEqual(self.db.setting('setup_completed','0'),'0')
        with self.db.conn:
            self.db.set_setting('setup_completed','1'); self.db.conn.execute("insert into setup_systems(system_id,emulator_mode,validation_status,updated_at) values('game_boy','later','needs setup',0)"); self.db.conn.execute("insert into setup_directories(system_id,path) values('game_boy','/tmp/invalid')")
            self.db.conn.execute("insert into setup_directories(system_id,path) values('game_boy','/tmp/second')")
        self.assertEqual(self.db.conn.execute("select count(*) from setup_directories where system_id='game_boy'").fetchone()[0],2); self.assertEqual(self.db.setting('setup_completed'),'1')
    def test_legacy_sqlite_database_migrates_without_data_loss(self):
        legacy=Path(self.tmp.name)/'legacy.sqlite3'; import sqlite3
        conn=sqlite3.connect(legacy); conn.executescript("CREATE TABLE games(id INTEGER PRIMARY KEY,title TEXT NOT NULL,filename TEXT NOT NULL,path TEXT UNIQUE NOT NULL,system TEXT NOT NULL,extension TEXT NOT NULL,size INTEGER NOT NULL DEFAULT 0,mtime REAL NOT NULL DEFAULT 0,available INTEGER NOT NULL DEFAULT 1,emulator TEXT,core_path TEXT,favorite INTEGER NOT NULL DEFAULT 0,last_played REAL,launch_count INTEGER NOT NULL DEFAULT 0); INSERT INTO games(title,filename,path,system,extension) VALUES('Legacy Game','legacy.nes','/tmp/legacy.nes','NES','.nes');"); conn.commit();conn.close()
        upgraded=Database(legacy); self.assertEqual(upgraded.conn.execute('select title from games').fetchone()[0],'Legacy Game'); self.assertEqual(upgraded.conn.execute('pragma user_version').fetchone()[0],4); self.assertIsNotNone(upgraded.conn.execute('select * from setup_systems').fetchone() if False else upgraded.conn.execute("select name from sqlite_master where name='system_catalog'").fetchone()); upgraded.close()

if __name__=='__main__': unittest.main()
