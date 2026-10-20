from __future__ import annotations
import os, sys, time, subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent
from PySide6.QtWidgets import *
from .database import Database
from .scanner import scan_directory
from .launcher import launch
from .picker import SystemPicker
from .scanner import ScanControl
from .discovery import mounted_volumes, likely_roots, discover_emulators
from .backup import backup_database, restore_database
from .setup_wizard import SetupWizard
from .audio import AudioManager
from .controller import ControllerBridge

if os.name == 'nt':
    APPDATA=Path(os.environ.get('APPDATA',Path.home()/'AppData/Roaming'))/'RetroDeck'
else:
    APPDATA=Path(os.environ.get('XDG_DATA_HOME',Path.home()/'.local/share'))/'retrodeck'
class ScanWorker(QThread):
    done=Signal(int,str)
    progress=Signal(int,str)
    def __init__(self,db,dirid,root): super().__init__(); self.db=db; self.dirid=dirid; self.root=root; self.control=ScanControl()
    def run(self): self.done.emit(*scan_directory(self.db,self.dirid,self.root,control=self.control,progress=lambda n,p:self.progress.emit(n,p)))
class RetroDeck(QMainWindow):
    def __init__(self):
        super().__init__(); self.db=Database(APPDATA/'library.sqlite3'); self.audio=AudioManager(Path(__file__).parent.parent/'assets', enabled=self.db.setting('audio_enabled','1')=='1', volume=float(self.db.setting('audio_volume','0.24'))); self.controller=ControllerBridge(self); self.controller.action.connect(self.controller_action); self.installEventFilter(self); self.setWindowTitle('RetroDeck'); self.resize(1120,720); self.setMinimumSize(900,560); self.workers=[]
        self.setStyleSheet('''QMainWindow,QWidget{background:#080b14;color:#f0f4ff;font-size:13px} QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #262052,stop:.55 #182d52,stop:1 #123e58);color:#ffffff;border:1px solid #665dca;border-radius:7px;padding:9px 14px} QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #533fa4,stop:.55 #17658b,stop:1 #13a6bd);border:1px solid #76efff;color:#ffffff} QLineEdit,QComboBox,QTextEdit{background:#10182a;color:#f3f6ff;border:1px solid #344a78;border-radius:7px;padding:8px} QLineEdit:focus,QComboBox:focus,QTextEdit:focus{border:1px solid #6eeaff} QListWidget,QTableWidget{background:#0d1626;color:#e8edf2;border:1px solid #2e4271;gridline-color:#26385e;border-radius:10px} QListWidget#nav{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #11152a,stop:1 #0a1020);border:1px solid #30326e;padding:12px;border-radius:14px} QListWidget#nav::item{padding:12px 10px;border-radius:8px;color:#9aaed1} QListWidget#nav::item:selected{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4d2d95,stop:.7 #164e70,stop:1 #0d8393);color:#b5f8ff;border-left:4px solid #ff55e8} QListWidget#nav::item:hover{background:#25204f;color:#ffffff} QHeaderView::section{background:#202451;color:#c4c8ff;padding:9px;border:0} QLabel#title{font-size:28px;font-weight:bold;color:#ffffff} QLabel#eyebrow{font-size:11px;font-weight:bold;color:#71efff;letter-spacing:2px} QLabel#hero{font-size:30px;font-weight:bold;color:#ffffff} QLabel#metric{font-size:24px;font-weight:bold;color:#d18cff} QTabWidget::pane{border:0} QScrollBar:vertical{background:#0b1020;width:10px} QScrollBar::handle:vertical{background:#633db1;border-radius:5px} QScrollBar::handle:vertical:hover{background:#e149d2}''')
        self.tabs=QTabWidget(); self.build_home(); self.build_library(); self.build_systems(); self.build_scan(); self.build_settings(); self.tabs.tabBar().hide()
        shell=QWidget(); shell_layout=QHBoxLayout(shell); shell_layout.setContentsMargins(18,18,18,18); shell_layout.setSpacing(16)
        side=QWidget(); side_layout=QVBoxLayout(side); side_layout.setContentsMargins(0,0,0,0); self.nav=QListWidget(); self.nav.setObjectName('nav'); self.nav.setFixedWidth(190); self.nav.setSpacing(5)
        for label in ('⌂  Home','▦  Game Library','◈  Systems','◌  Scan & Import','⚙  Settings'): self.nav.addItem(label)
        self.nav.currentRowChanged.connect(self.on_nav_changed); side_layout.addWidget(self.nav)
        self.audio_toggle=QPushButton('♫  Ambient On' if self.audio.enabled else '♫  Ambient Off'); self.audio_toggle.clicked.connect(self.toggle_audio); side_layout.addWidget(self.audio_toggle)
        self.audio_volume=QSlider(Qt.Horizontal); self.audio_volume.setRange(0,100); self.audio_volume.setValue(int(self.audio.volume*100)); self.audio_volume.setToolTip('Ambient volume'); self.audio_volume.valueChanged.connect(self.set_audio_volume); side_layout.addWidget(self.audio_volume)
        side_layout.addWidget(QLabel('NEON AUDIO'))
        self.nav.setCurrentRow(0); shell_layout.addWidget(side); shell_layout.addWidget(self.tabs,1); self.setCentralWidget(shell); self.audio.play_music()
    def on_nav_changed(self,row): self.tabs.setCurrentIndex(row); self.audio.play_confirm()
    def toggle_audio(self):
        enabled=self.audio.toggle(); self.db.set_setting('audio_enabled','1' if enabled else '0'); self.audio_toggle.setText('♫  Ambient On' if enabled else '♫  Ambient Off'); self.audio.play_confirm()
    def set_audio_volume(self,value): self.audio.set_volume(value/100); self.db.set_setting('audio_volume',str(value/100))
    def controller_action(self,action):
        if action=='up': self.nav.setCurrentRow(max(0,self.nav.currentRow()-1))
        elif action=='down': self.nav.setCurrentRow(min(self.nav.count()-1,self.nav.currentRow()+1))
        elif action=='accept':
            if self.tabs.currentIndex()==1 and self.library_stack.currentIndex()==1 and self.grid_layout.count():
                widget=self.grid_layout.itemAt(0).widget(); button=widget.findChild(QPushButton); button.click() if button else None
            elif self.tabs.currentIndex()==1: self.play_selected()
        elif action=='back': self.nav.setCurrentRow(0)
        self.audio.play_confirm()
    def eventFilter(self,obj,event):
        if event.type()==QEvent.KeyPress:
            key=event.key(); mapping={Qt.Key_Up:'up',Qt.Key_Down:'down',Qt.Key_Return:'accept',Qt.Key_Enter:'accept',Qt.Key_Escape:'back'}
            if key in mapping: self.controller_action(mapping[key]); return True
        return super().eventFilter(obj,event)
    def build_home(self):
        w=QWidget(); l=QVBoxLayout(w); l.setSpacing(16); eyebrow=QLabel('RETRODECK INFINITY  /  COMMAND CENTER'); eyebrow.setObjectName('eyebrow'); l.addWidget(eyebrow); title=QLabel('Your collection,\nbeautifully organized.'); title.setObjectName('hero'); l.addWidget(title)
        hero=QFrame(); hero.setStyleSheet('QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #24124b,stop:.38 #3d1766,stop:.7 #123c68,stop:1 #071f36);border:1px solid #a64fff;border-radius:16px}'); hl=QVBoxLayout(hero); welcome=QLabel('✦  READY WHEN YOU ARE  /  SYSTEM ONLINE'); welcome.setObjectName('eyebrow');hl.addWidget(welcome); self.home_summary=QLabel();self.home_summary.setWordWrap(True);hl.addWidget(self.home_summary); actions=QHBoxLayout(); scan=QPushButton('⚡  Scan My Drives');scan.clicked.connect(self.scan_all);mounts=QPushButton('◉  Refresh mounted volumes');mounts.clicked.connect(self.refresh_home);actions.addWidget(scan);actions.addWidget(mounts);actions.addStretch();hl.addLayout(actions);l.addWidget(hero)
        metrics=QHBoxLayout()
        self.metric_cards=[]
        for label in ('GAMES INDEXED','PLAYABLE','SYSTEMS','MOUNTED VOLUMES'):
            card=QFrame();card.setStyleSheet('QFrame{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #121934,stop:1 #17102d);border:1px solid #4a3e9b;border-radius:12px} QFrame:hover{border:1px solid #e052e8}');cl=QVBoxLayout(card);v=QLabel('—');v.setObjectName('metric');cl.addWidget(v);cl.addWidget(QLabel(label));metrics.addWidget(card);self.metric_cards.append(v)
        l.addLayout(metrics); section=QLabel('ACTIVITY & STORAGE');section.setObjectName('eyebrow');l.addWidget(section);self.home_log=QTextEdit();self.home_log.setReadOnly(True);self.home_log.setMaximumHeight(180);l.addWidget(self.home_log);l.addStretch(); self.tabs.addTab(w,'Home'); self.refresh_home()
    def refresh_home(self):
        games=self.db.conn.execute('SELECT count(*) FROM games').fetchone()[0]; playable=self.db.conn.execute('SELECT count(*) FROM games WHERE available=1').fetchone()[0]; systems=self.db.conn.execute('SELECT count(DISTINCT system) FROM games').fetchone()[0]; vols=mounted_volumes(); emus=discover_emulators(self.db.conn.execute("SELECT executable FROM emulator_definitions WHERE name='RetroArch'").fetchone()['executable'])
        found=sum(1 for e in emus if e['available']); self.home_summary.setText(f'<b>{games}</b> games indexed  •  <b>{playable}</b> ready to play  •  <b>{systems}</b> systems represented  •  <b>{found}</b> emulator installations detected')
        for label,value in zip(self.metric_cards,(games,playable,systems,len(vols))): label.setText(str(value))
        self.home_log.setPlainText('Mounted volumes:\n'+'\n'.join(f"  {v['path']}  [{v['filesystem']}]  {'accessible' if v['accessible'] else 'inaccessible'}" for v in vols) or 'No eligible mounted volumes detected.')
    def build_library(self):
        w=QWidget(); l=QVBoxLayout(w); head=QHBoxLayout(); t=QLabel('GAME VAULT'); t.setObjectName('title'); head.addWidget(t); head.addStretch(); self.search=QLineEdit(); self.search.setPlaceholderText('Search your library…'); self.search.textChanged.connect(self.refresh_games); head.addWidget(self.search); self.sysfilter=QComboBox(); self.sysfilter.addItem('All systems'); self.sysfilter.addItems(self.db.conn.execute('SELECT name FROM systems ORDER BY name').fetchall()[i]['name'] for i in range(self.db.conn.execute('SELECT count(*) FROM systems').fetchone()[0])); self.sysfilter.currentTextChanged.connect(self.refresh_games); head.addWidget(self.sysfilter); self.grid_button=QPushButton('▦  Box View'); self.grid_button.clicked.connect(self.toggle_library_view); head.addWidget(self.grid_button); l.addLayout(head)
        bar=QHBoxLayout(); self.status=QLabel('Ready. No artwork or network services are required.'); bar.addWidget(self.status); bar.addStretch(); b=QPushButton('Rescan enabled folders'); b.clicked.connect(self.scan_all); bar.addWidget(b); l.addLayout(bar)
        self.library_stack=QStackedWidget(); self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(['Title','System','Format','Size','Availability','Favorite','Assigned']); self.table.horizontalHeader().setStretchLastSection(True); self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.doubleClicked.connect(self.play_selected); self.library_stack.addWidget(self.table)
        self.grid_scroll=QScrollArea(); self.grid_scroll.setWidgetResizable(True); self.grid_scroll.setAlignment(Qt.AlignTop|Qt.AlignLeft); self.grid_host=QWidget(); self.grid_layout=QGridLayout(self.grid_host); self.grid_layout.setSpacing(14); self.grid_scroll.setWidget(self.grid_host); self.library_stack.addWidget(self.grid_scroll); l.addWidget(self.library_stack); self.tabs.addTab(w,'Library'); self.refresh_games()
    def refresh_games(self):
        sysn='' if self.sysfilter.currentText()=='All systems' else self.sysfilter.currentText(); rows=self.db.list_games(self.search.text(),sysn)
        self.table.setRowCount(0)
        for g in rows:
            r=self.table.rowCount(); self.table.insertRow(r); vals=[g['title'],g['system'],g['extension'],self.size(g['size']),'Available' if g['available'] else 'Missing','★' if g['favorite'] else '',g['emulator'] or 'Auto']
            for c,v in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(str(v)))
            self.table.item(r,0).setData(Qt.UserRole,dict(g))
        while self.grid_layout.count(): item=self.grid_layout.takeAt(0); item.widget().deleteLater() if item.widget() else None
        for i,g in enumerate(rows):
            card=QFrame(); card.setFixedSize(250,320); card.setStyleSheet('QFrame#gamebox{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #202044,stop:.5 #151c39,stop:1 #0d3550);border:1px solid #594aa8;border-radius:13px} QFrame#gamebox:hover{border:2px solid #63efff;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #39205f,stop:.55 #162d5b,stop:1 #0d5262)}')
            card.setObjectName('gamebox'); cl=QVBoxLayout(card); badge=QLabel('◈  '+str(g['system']).upper()); badge.setStyleSheet('color:#73edff;font-size:10px;font-weight:bold;letter-spacing:1px'); cl.addWidget(badge); art=QLabel('◆\n'+str(g['title'])); art.setAlignment(Qt.AlignCenter); art.setMinimumHeight(140); art.setStyleSheet('color:#ffffff;font-size:17px;font-weight:bold;background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #32165f,stop:.5 #112854,stop:1 #0d6671);border:1px solid #b15be8;border-radius:8px;padding:12px'); cl.addWidget(art); meta=QLabel(f"{g['extension']}  •  {'READY' if g['available'] else 'MISSING'}");meta.setStyleSheet('color:#aebbd6');cl.addWidget(meta); play=QPushButton('▶  Play');play.clicked.connect(lambda _,game=dict(g):self.play_game(game));cl.addWidget(play);self.grid_layout.addWidget(card,i//4,i%4)
    def size(self,n):
        for u in ['B','KB','MB','GB']:
            if n<1024:return f'{n:.0f} {u}'
            n/=1024
        return f'{n:.1f} TB'
    def selected_game(self):
        r=self.table.currentRow(); return self.table.item(r,0).data(Qt.UserRole) if r>=0 else None
    def toggle_library_view(self):
        grid=self.library_stack.currentIndex()==0; self.library_stack.setCurrentIndex(1 if grid else 0); self.grid_button.setText('☷  List View' if grid else '▦  Box View')
    def play_selected(self): self.play_game(self.selected_game())
    def play_game(self,g):
        if not g: return
        em=self.db.conn.execute('SELECT * FROM emulator_definitions WHERE name=?',(self.pick_emulator(g),)).fetchone()
        if not em: QMessageBox.warning(self,'Cannot launch','No emulator is configured for this game. Configure one in Settings.'); return
        core=None
        if em['name']=='RetroArch':
            c=self.db.conn.execute('SELECT library_path FROM retroarch_cores WHERE enabled=1 AND (extensions LIKE ? OR systems LIKE ?) LIMIT 1',('%'+g['extension']+'%','%'+g['system']+'%')).fetchone(); core=c['library_path'] if c else None
        try:
            proc,cmd=launch(self.db,g,em,core); self.status.setText(f'Launch attempted (PID {proc.pid}): {g["title"]}'); self.audio.play_confirm(); self.refresh_games()
        except Exception as e: QMessageBox.critical(self,'Launch failed',str(e)); self.status.setText('Launch failed: '+str(e))
    def pick_emulator(self,g):
        if g['system'] in ('PS2',): return 'PCSX2'
        if g['system'] in ('GameCube','Wii'): return 'Dolphin'
        if g['system']=='Wii U': return 'Cemu'
        return 'RetroArch'
    def build_systems(self):
        w=QWidget(); l=QVBoxLayout(w); head=QHBoxLayout(); head.addWidget(QLabel('Systems and configured game roots')); head.addStretch(); picker=QPushButton('Universal System Picker'); picker.setToolTip('Browse and add from the full RetroArch system catalog'); picker.clicked.connect(self.open_picker); head.addWidget(picker); l.addLayout(head); self.dirtable=QTableWidget(0,6); self.dirtable.setHorizontalHeaderLabels(['System','Folder','Enabled','Last scan','Games','Accessible']); self.dirtable.horizontalHeader().setStretchLastSection(True); l.addWidget(self.dirtable); bb=QHBoxLayout(); add=QPushButton('Add folder'); add.clicked.connect(self.add_folder); scan=QPushButton('Scan selected'); scan.clicked.connect(self.scan_selected); rem=QPushButton('Remove'); rem.clicked.connect(self.remove_folder); bb.addWidget(add);bb.addWidget(scan);bb.addWidget(rem);bb.addStretch();l.addLayout(bb); self.tabs.addTab(w,'Systems'); self.refresh_dirs()

    def open_picker(self):
        dialog=SystemPicker(self.db,self)
        if dialog.exec():
            self.refresh_dirs(); self.refresh_games(); self.sysfilter.clear(); self.sysfilter.addItem('All systems'); self.sysfilter.addItems([r['name'] for r in self.db.conn.execute('SELECT name FROM systems ORDER BY name')])
    def refresh_dirs(self):
        rows=self.db.conn.execute('SELECT * FROM game_directories ORDER BY system,priority,path').fetchall(); self.dirtable.setRowCount(0)
        for d in rows:
            r=self.dirtable.rowCount();self.dirtable.insertRow(r)
            vals=[d['system'],d['path'],'Yes' if d['enabled'] else 'No',time.strftime('%Y-%m-%d %H:%M',time.localtime(d['last_scan'])) if d['last_scan'] else 'Never',d['game_count'],'Yes' if Path(d['path']).is_dir() else 'No']
            for c,v in enumerate(vals):self.dirtable.setItem(r,c,QTableWidgetItem(str(v)))
            self.dirtable.item(r,1).setData(Qt.UserRole,d['id'])
    def add_folder(self):
        p=QFileDialog.getExistingDirectory(self,'Choose a game folder');
        if not p:return
        system,ok=QInputDialog.getItem(self,'Assign system','System:',[r['name'] for r in self.db.conn.execute('SELECT name FROM systems ORDER BY name')],0,False)
        if ok:
            with self.db.conn:self.db.conn.execute('INSERT OR IGNORE INTO game_directories(system,path) VALUES(?,?)',(system,p))
            self.refresh_dirs()
    def scan_selected(self):
        r=self.dirtable.currentRow();
        if r<0:return
        did=self.dirtable.item(r,1).data(Qt.UserRole); d=self.db.conn.execute('SELECT * FROM game_directories WHERE id=?',(did,)).fetchone(); self.start_scan(d)
    def scan_all(self):
        for d in self.db.conn.execute('SELECT * FROM game_directories WHERE enabled=1'):self.start_scan(d)
    def start_scan(self,d):
        self.status.setText('Scanning '+d['path']); w=ScanWorker(self.db,d['id'],d['path']); w.done.connect(lambda n,e:self.scan_done(n,e)); w.progress.connect(lambda n,p:self.scan_progress(n,p)); w.finished.connect(lambda:self.workers.remove(w) if w in self.workers else None); self.workers.append(w); self.active_worker=w; w.start()
    def scan_progress(self,n,p): self.status.setText(f'Scanning: {n} candidates — {p}'); self.scan_count.setText(f'Files/candidates found: {n}'); self.scan_current.setText(p)
    def scan_done(self,n,e): self.status.setText(f'Scan complete: {n} games'+((' — '+e) if e else '')); self.scan_log.append(f'{time.strftime("%H:%M:%S")}  {n} games — {e or "complete"}'); self.refresh_dirs(); self.refresh_games(); self.refresh_home()
    def remove_folder(self):
        r=self.dirtable.currentRow();
        if r<0:return
        did=self.dirtable.item(r,1).data(Qt.UserRole)
        with self.db.conn:self.db.conn.execute('DELETE FROM game_directories WHERE id=?',(did,))
        self.refresh_dirs()
    def build_scan(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('Scan & Import')); info=QLabel('Scans run in a background worker. Mounted-volume discovery is read-only and never scans system directories by default.');info.setWordWrap(True);l.addWidget(info)
        self.scan_count=QLabel('Files/candidates found: 0'); self.scan_current=QLabel('Current path: idle'); l.addWidget(self.scan_count); l.addWidget(self.scan_current); bb=QHBoxLayout(); pause=QPushButton('Pause'); pause.clicked.connect(lambda:self.active_worker.control.pause() if hasattr(self,'active_worker') and self.active_worker.isRunning() else None); resume=QPushButton('Resume'); resume.clicked.connect(lambda:self.active_worker.control.resume() if hasattr(self,'active_worker') and self.active_worker.isRunning() else None); cancel=QPushButton('Cancel'); cancel.clicked.connect(lambda:self.active_worker.control.cancel() if hasattr(self,'active_worker') and self.active_worker.isRunning() else None); refresh=QPushButton('Refresh mounts'); refresh.clicked.connect(self.refresh_home); bb.addWidget(pause);bb.addWidget(resume);bb.addWidget(cancel);bb.addWidget(refresh);bb.addStretch();l.addLayout(bb); self.scan_log=QTextEdit();self.scan_log.setReadOnly(True);l.addWidget(self.scan_log); self.tabs.addTab(w,'Scan & Import')
    def build_settings(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('Emulator Manager'))
        controls=QHBoxLayout(); detect=QPushButton('Re-detect installations'); detect.clicked.connect(self.redetect_emulators); backup=QPushButton('Back up database'); backup.clicked.connect(self.backup_db); restore=QPushButton('Restore database'); restore.clicked.connect(self.restore_db); rerun=QPushButton('Run setup wizard again'); rerun.clicked.connect(self.rerun_setup); controls.addWidget(detect);controls.addWidget(backup);controls.addWidget(restore);controls.addWidget(rerun);controls.addStretch();l.addLayout(controls)
        self.emutable=QTableWidget(0,7);self.emutable.setHorizontalHeaderLabels(['Emulator','Executable path','Working directory','Arguments','Launch method','Status','Actions']);self.emutable.horizontalHeader().setStretchLastSection(True);self.emutable.itemChanged.connect(self.save_emulator_cell);l.addWidget(self.emutable)
        for e in self.db.conn.execute('SELECT * FROM emulator_definitions ORDER BY name'):
            r=self.emutable.rowCount();self.emutable.insertRow(r); values=(e['name'],e['executable'],e['working_directory'],e['default_args'],e['launch_method'],self.exestatus(e['executable']))
            for c,value in enumerate(values): self.emutable.setItem(r,c,QTableWidgetItem(str(value)))
            b=QPushButton('Browse'); b.clicked.connect(lambda _,row=r:self.browse_emulator(row)); self.emutable.setCellWidget(r,6,b)
        l.addWidget(QLabel('RetroArch Core Manager'))
        self.coretable=QTableWidget(0,4); self.coretable.setHorizontalHeaderLabels(['Core name','Library path','Extensions / systems','Status']); self.coretable.horizontalHeader().setStretchLastSection(True); l.addWidget(self.coretable)
        cb=QHBoxLayout(); add=QPushButton('Add core'); add.clicked.connect(self.add_core); edit=QPushButton('Edit selected'); edit.clicked.connect(self.edit_core); remove=QPushButton('Remove selected'); remove.clicked.connect(self.remove_core); cb.addWidget(add); cb.addWidget(edit); cb.addWidget(remove); cb.addStretch(); l.addLayout(cb); self.refresh_cores()
        self.tabs.addTab(w,'Settings');
    def exestatus(self,p):
        return 'available' if Path(p).is_file() and (os.name=='nt' or os.access(p,os.X_OK)) else ('missing' if not Path(p).exists() else 'not executable')
    def save_emulator_cell(self,item):
        if item.column() not in (1,2,3,4) or not item.text(): return
        row=item.row(); name=self.emutable.item(row,0).text(); columns={1:'executable',2:'working_directory',3:'default_args',4:'launch_method'}
        with self.db.conn: self.db.conn.execute(f"UPDATE emulator_definitions SET {columns[item.column()]}=? WHERE name=?",(item.text(),name))
    def browse_emulator(self,row):
        p,_=QFileDialog.getOpenFileName(self,'Select emulator executable');
        if p:
            name=self.emutable.item(row,0).text();
            with self.db.conn:self.db.conn.execute('UPDATE emulator_definitions SET executable=?,status=? WHERE name=?',(p,self.exestatus(p),name))
            self.emutable.setItem(row,1,QTableWidgetItem(p));self.emutable.setItem(row,5,QTableWidgetItem(self.exestatus(p)))
    def refresh_cores(self):
        self.coretable.setRowCount(0)
        for c in self.db.conn.execute('SELECT * FROM retroarch_cores ORDER BY name'):
            r=self.coretable.rowCount(); self.coretable.insertRow(r)
            for col,val in enumerate((c['name'],c['library_path'],c['extensions']+' / '+c['systems'], 'available' if Path(c['library_path']).is_file() else 'missing')): self.coretable.setItem(r,col,QTableWidgetItem(str(val)))
            self.coretable.item(r,0).setData(Qt.UserRole,c['id'])
    def add_core(self):
        name,ok=QInputDialog.getText(self,'Add RetroArch core','Display name:')
        if not ok or not name:return
        lib,_=QFileDialog.getOpenFileName(self,'Select core library')
        if not lib:return
        ext,_=QInputDialog.getText(self,'Core mapping','Extensions (comma-separated):',text='.rom')
        systems,_=QInputDialog.getText(self,'Core mapping','Systems (comma-separated):')
        with self.db.conn:self.db.conn.execute('INSERT OR REPLACE INTO retroarch_cores(name,library_path,extensions,systems) VALUES(?,?,?,?)',(name,lib,ext,systems))
        self.refresh_cores()
    def edit_core(self):
        r=self.coretable.currentRow()
        if r<0:return
        cid=self.coretable.item(r,0).data(Qt.UserRole); c=self.db.conn.execute('SELECT * FROM retroarch_cores WHERE id=?',(cid,)).fetchone()
        name,ok=QInputDialog.getText(self,'Edit core','Display name:',text=c['name'])
        if ok and name:
            with self.db.conn:self.db.conn.execute('UPDATE retroarch_cores SET name=? WHERE id=?',(name,cid))
            self.refresh_cores()
    def remove_core(self):
        r=self.coretable.currentRow()
        if r<0:return
        cid=self.coretable.item(r,0).data(Qt.UserRole)
        with self.db.conn:self.db.conn.execute('DELETE FROM retroarch_cores WHERE id=?',(cid,))
        self.refresh_cores()
    def redetect_emulators(self):
        exe=self.db.conn.execute("SELECT executable FROM emulator_definitions WHERE name='RetroArch'").fetchone(); found=discover_emulators(exe['executable'] if exe else '')
        available=[e for e in found if e['available']]; QMessageBox.information(self,'Emulator detection',f'Detected {len(available)} usable targeted installation(s).\n\n'+'\n'.join(f"{e['name']}: {e['path']}" for e in available) or 'No verified installations found.')
    def backup_db(self):
        path,_=QFileDialog.getSaveFileName(self,'Back up RetroDeck database',str(self.db.path.with_suffix('.sqlite3.backup')),'SQLite backup (*.backup *.sqlite3)')
        if path:
            backup_database(self.db,path); QMessageBox.information(self,'Backup complete',f'Backup written to:\n{path}')
    def restore_db(self):
        path,_=QFileDialog.getOpenFileName(self,'Restore RetroDeck database','','SQLite database (*.sqlite3 *.backup);;All files (*)')
        if path and QMessageBox.question(self,'Restore database','Create a safety backup and replace the current library?')==QMessageBox.Yes:
            try: old=restore_database(self.db,path); self.db=Database(APPDATA/'library.sqlite3'); self.refresh_games(); self.refresh_dirs(); self.refresh_home(); QMessageBox.information(self,'Restore complete',f'Previous database preserved at:\n{old}')
            except Exception as e: QMessageBox.critical(self,'Restore failed',str(e))
    def rerun_setup(self):
        wizard=SetupWizard(self.db,self)
        if wizard.exec(): self.refresh_dirs(); self.refresh_games(); self.refresh_home(); self.scan_all()
    def closeEvent(self,e): self.controller.close(); self.audio.close(); self.db.close();e.accept()
def main():
    app=QApplication(sys.argv); app.setApplicationName('RetroDeck'); win=RetroDeck();
    if win.db.setting('setup_completed')!='1':
        wizard=SetupWizard(win.db,win); wizard.exec(); win.refresh_dirs(); win.refresh_games(); win.refresh_home()
        if win.db.setting('setup_skipped')!='1': win.scan_all()
    win.show();sys.exit(app.exec())
