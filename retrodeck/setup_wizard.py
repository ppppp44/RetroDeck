from __future__ import annotations
import os, time
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog,QWidget,QVBoxLayout,QHBoxLayout,QStackedWidget,QLabel,QPushButton,QLineEdit,QListWidget,QListWidgetItem,QFileDialog,QComboBox,QTableWidget,QTableWidgetItem,QTextEdit,QMessageBox,QAbstractItemView
from .catalog import CATALOG, CatalogSystem
from .core_discovery import discover_cores, core_matches
from .discovery import mounted_volumes, likely_roots, discover_emulators

class SetupWizard(QDialog):
    def __init__(self,db,parent=None):
        super().__init__(parent); self.db=db; self.setWindowTitle('RetroDeck Infinity Setup'); self.resize(980,680); self.selected=[]; self.paths={}; self.config={}; self.cores=[]; self.emus=[]; self.page=QStackedWidget(); self.setStyleSheet('QDialog,QWidget{background:#111521;color:#e9eef7} QLabel#brand{font-size:30px;font-weight:bold;color:#71dcff} QLabel#heading{font-size:22px;font-weight:bold;color:#b9a7ff} QLineEdit,QComboBox,QListWidget,QTableWidget{background:#1b2231;color:#eef;border:1px solid #3d4a63;border-radius:5px;padding:6px} QPushButton{background:#29344a;color:#f5f7ff;border:1px solid #53688d;border-radius:6px;padding:9px 15px} QPushButton:hover{background:#3b4a68}')
        self.build_welcome(); self.build_systems(); self.build_paths(); self.build_emulators(); self.build_review(); root=QVBoxLayout(self); root.addWidget(self.page); nav=QHBoxLayout(); self.back=QPushButton('Back'); self.back.clicked.connect(self.previous); self.next=QPushButton('Continue'); self.next.clicked.connect(self.next_page); cancel=QPushButton('Configure Later'); cancel.clicked.connect(self.configure_later); nav.addWidget(self.back);nav.addStretch();nav.addWidget(cancel);nav.addWidget(self.next);root.addLayout(nav); self.update_nav(); self.load_existing()
    def build_welcome(self):
        w=QWidget();l=QVBoxLayout(w); brand=QLabel('RETRODECK INFINITY');brand.setObjectName('brand');l.addWidget(brand);l.addSpacing(20); h=QLabel('Set up your personal game command center');h.setObjectName('heading');l.addWidget(h); body=QLabel('This guided setup will help you choose systems, locate game folders, discover installed emulators and RetroArch cores, and build your library. Nothing is downloaded or changed in your game folders.');body.setWordWrap(True);l.addWidget(body);l.addStretch(); self.welcome_status=QLabel('Your existing library and configuration will be preserved.');l.addWidget(self.welcome_status);self.page.addWidget(w)
    def build_systems(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('Choose your gaming systems',objectName='heading'));self.system_search=QLineEdit();self.system_search.setPlaceholderText('Search systems…');self.system_search.textChanged.connect(self.refresh_systems);l.addWidget(self.system_search);self.systems=QListWidget();self.systems.setSelectionMode(QAbstractItemView.MultiSelection);self.systems.itemSelectionChanged.connect(self.selection_changed);l.addWidget(self.systems);b=QHBoxLayout();a=QPushButton('Select All');a.clicked.connect(lambda:self.select_filtered(True));c=QPushButton('Clear Selection');c.clicked.connect(lambda:self.select_filtered(False));self.selected_label=QLabel('0 systems selected');b.addWidget(a);b.addWidget(c);b.addStretch();b.addWidget(self.selected_label);l.addLayout(b);self.page.addWidget(w);self.refresh_systems()
    def refresh_systems(self):
        keep={x.system_id for x in self.selected}; text=self.system_search.text().casefold(); self.systems.clear()
        for s in CATALOG:
            if text and text not in ' '.join((s.name,s.category,s.manufacturer,s.system_id,*s.aliases)).casefold():continue
            item=QListWidgetItem(f'{s.name}   ·   {s.category}');item.setData(Qt.UserRole,s.system_id);self.systems.addItem(item);item.setSelected(s.system_id in keep)
    def selection_changed(self): self.selected=[next(s for s in CATALOG if s.system_id==i.data(Qt.UserRole)) for i in self.systems.selectedItems()];self.selected_label.setText(f'{len(self.selected)} systems selected')
    def select_filtered(self,yes):
        for i in range(self.systems.count()):self.systems.item(i).setSelected(yes)
        self.selection_changed()
    def build_paths(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('Where are your games stored?',objectName='heading'));self.path_system=QComboBox();self.path_system.currentIndexChanged.connect(self.refresh_paths);l.addWidget(self.path_system);self.path_table=QTableWidget(0,3);self.path_table.setHorizontalHeaderLabels(['Folder','Accessible','Candidate files']);self.path_table.horizontalHeader().setStretchLastSection(True);l.addWidget(self.path_table);b=QHBoxLayout();add=QPushButton('Browse for Folder');add.clicked.connect(self.add_path);remove=QPushButton('Remove Folder');remove.clicked.connect(self.remove_path);suggest=QPushButton('Detect Mounted Drives');suggest.clicked.connect(self.suggest_paths);b.addWidget(add);b.addWidget(remove);b.addWidget(suggest);b.addStretch();l.addLayout(b);self.path_hint=QLabel('Each selected system can have multiple independent folders.');l.addWidget(self.path_hint);self.page.addWidget(w)
    def refresh_paths(self):
        self.path_table.setRowCount(0); sid=self.path_system.currentData() if self.path_system.count() else None
        for p in self.paths.get(sid,[]):
            r=self.path_table.rowCount();self.path_table.insertRow(r); accessible=Path(p).is_dir() and os.access(p,os.R_OK); count='calculated' if accessible else 'unavailable'; self.path_table.setItem(r,0,QTableWidgetItem(p));self.path_table.setItem(r,1,QTableWidgetItem('Yes' if accessible else 'No'));self.path_table.setItem(r,2,QTableWidgetItem(count))
    def add_path(self):
        p=QFileDialog.getExistingDirectory(self,'Choose game folder');sid=self.path_system.currentData()
        if p and sid and p not in self.paths.setdefault(sid,[]):self.paths[sid].append(p);self.refresh_paths()
    def remove_path(self):
        r=self.path_table.currentRow();sid=self.path_system.currentData()
        if r>=0 and sid:self.paths[sid].pop(r);self.refresh_paths()
    def suggest_paths(self):
        roots=[str(p) for p in likely_roots(mounted_volumes())];sid=self.path_system.currentData(); candidates=[p for p in roots if p not in self.paths.setdefault(sid,[])];
        if candidates:
            p,ok=__import__('PySide6.QtWidgets',fromlist=['QInputDialog']).QInputDialog.getItem(self,'Suggested folders','Choose a verified accessible folder:',candidates,0,False)
            if ok:self.paths[sid].append(p);self.refresh_paths()
        else: QMessageBox.information(self,'No suggestions','No accessible likely game folders were found. Use Browse for Folder.')
    def build_emulators(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('How should RetroDeck launch these systems?',objectName='heading'));self.emu_system=QComboBox();self.emu_system.currentIndexChanged.connect(self.refresh_emu);l.addWidget(self.emu_system);self.mode=QComboBox();self.mode.addItems(['Recommended installed core/emulator','RetroArch core','Standalone emulator','Configure later']);self.mode.currentTextChanged.connect(self.refresh_emu_options);l.addWidget(self.mode);self.emu_choice=QComboBox();l.addWidget(self.emu_choice);self.emu_status=QLabel();self.emu_status.setWordWrap(True);l.addWidget(self.emu_status);l.addStretch();self.page.addWidget(w);self.refresh_emu_options()
    def refresh_emu(self): self.refresh_emu_options()
    def refresh_emu_options(self):
        self.emu_choice.clear(); sid=self.emu_system.currentData() if self.emu_system.count() else None; s=next((x for x in self.selected if x.system_id==sid),None); self.cores=discover_cores(self.db.conn.execute("SELECT executable FROM emulator_definitions WHERE name='RetroArch'").fetchone()['executable']);self.emus=discover_emulators(''); options=[]
        if 'Standalone' in self.mode.currentText(): options=[e['name']+' — '+e['path'] for e in self.emus if e['available']]
        elif 'core' in self.mode.currentText().lower() or 'Recommended' in self.mode.currentText(): options=[c['name']+' — '+c['library_path'] for c in self.cores if s and core_matches(s,c)]
        self.emu_choice.addItems(options or ['No verified compatible installation found']);self.emu_status.setText('Ready' if options else 'No compatible installation detected. You may configure this system later.')
    def build_review(self):
        w=QWidget();l=QVBoxLayout(w);l.addWidget(QLabel('Review your setup',objectName='heading'));self.review=QTextEdit();self.review.setReadOnly(True);l.addWidget(self.review);self.page.addWidget(w)
    def load_existing(self):
        if self.db.setting('setup_completed')=='1':
            ids=[r['system_id'] for r in self.db.conn.execute('SELECT system_id FROM setup_systems')];self.selected=[s for s in CATALOG if s.system_id in ids]
            for r in self.db.conn.execute('SELECT system_id,path FROM setup_directories'):self.paths.setdefault(r['system_id'],[]).append(r['path'])
    def update_nav(self): self.back.setEnabled(self.page.currentIndex()>0);self.next.setText('Finish Setup' if self.page.currentIndex()==4 else 'Continue')
    def next_page(self):
        i=self.page.currentIndex()
        if i==1 and not self.selected: QMessageBox.warning(self,'Choose systems','Select at least one system or choose Configure Later.');return
        if i==1:
            self.path_system.clear();self.path_system.addItems([s.name for s in self.selected]);[self.path_system.setItemData(i,s.system_id) for i,s in enumerate(self.selected)];self.refresh_paths()
        if i==2:
            self.emu_system.clear();self.emu_system.addItems([s.name for s in self.selected]);[self.emu_system.setItemData(i,s.system_id) for i,s in enumerate(self.selected)];self.refresh_emu_options()
        if i==3:
            self.config[self.emu_system.currentData()]={'mode':self.mode.currentText(),'choice':self.emu_choice.currentText()}
            self.make_review()
        if i<4:self.page.setCurrentIndex(i+1);self.update_nav()
        else:self.finish()
    def previous(self):
        if self.page.currentIndex()>0:self.page.setCurrentIndex(self.page.currentIndex()-1);self.update_nav()
    def make_review(self):
        lines=[]
        for s in self.selected:
            ps=self.paths.get(s.system_id,[]); lines.append(f'{s.name}\n  Game folders: {len(ps)}\n  Emulator/core: selected in the configuration step or Configure later\n  Status: {"Ready to scan" if ps else "Needs game folder"}')
        self.review.setPlainText('\n\n'.join(lines) or 'No systems selected.')
    def finish(self):
        now=time.time()
        with self.db.conn:
            self.db.set_setting('setup_completed','1');self.db.set_setting('setup_version','0.4.0')
            for s in self.selected:
                cfg=self.config.get(s.system_id,{}); choice=cfg.get('choice',''); mode=cfg.get('mode','Configure later'); core_path=choice.split(' — ',1)[1] if ' — ' in choice and 'core' in mode.lower() else ''; exe_path=choice.split(' — ',1)[1] if ' — ' in choice and 'Standalone' in mode else ''
                self.db.conn.execute('INSERT INTO setup_systems(system_id,emulator_mode,emulator_path,core_path,validation_status,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(system_id) DO UPDATE SET emulator_mode=excluded.emulator_mode,emulator_path=excluded.emulator_path,core_path=excluded.core_path,validation_status=excluded.validation_status,updated_at=excluded.updated_at',(s.system_id,mode,exe_path,core_path,'ready' if self.paths.get(s.system_id) and mode!='Configure later' else 'needs setup',now));
                for p in self.paths.get(s.system_id,[]):
                    self.db.conn.execute('INSERT OR IGNORE INTO setup_directories(system_id,path) VALUES(?,?)',(s.system_id,p));self.db.conn.execute('INSERT OR IGNORE INTO game_directories(system,path) VALUES(?,?)',(s.name,p))
        self.accept()
    def configure_later(self): self.db.set_setting('setup_completed','1');self.db.set_setting('setup_skipped','1');self.accept()
