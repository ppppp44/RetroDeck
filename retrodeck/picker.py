from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit, QLabel, QMessageBox
from .catalog import CATALOG, search_catalog, CatalogSystem
from .core_discovery import discover_cores, core_matches, discover_core_dirs

class SystemPicker(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent); self.db=db; self.setWindowTitle('Universal System Picker'); self.resize(1000,650); self.selected=set(); self.favorites=set(); self.cores=[]
        self.setStyleSheet('QDialog,QWidget{background:#14171c;color:#e8edf2} QLineEdit,QComboBox,QTextEdit{background:#20262e;color:#eef;border:1px solid #3b4652;padding:6px} QTableWidget{background:#1b2027;color:#e8edf2;gridline-color:#303946} QPushButton{background:#27313c;color:#eef;border:1px solid #3b4b5d;border-radius:5px;padding:7px 12px}')
        self.build(); self.refresh_cores(); self.refresh()
    def build(self):
        root=QVBoxLayout(self); top=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Search systems, aliases, manufacturers…'); self.search.textChanged.connect(self.refresh); top.addWidget(self.search)
        self.category=QComboBox(); self.category.addItem('All categories'); self.category.addItems(sorted({s.category for s in CATALOG})); self.category.currentTextChanged.connect(self.refresh); top.addWidget(self.category)
        self.sort=QComboBox(); self.sort.addItems(['Name','Manufacturer','Category','Installation status']); self.sort.currentTextChanged.connect(self.refresh); top.addWidget(self.sort)
        self.installed=QCheckBox('Installed only'); self.installed.stateChanged.connect(self.refresh); top.addWidget(self.installed); root.addLayout(top)
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(['Add','System','Manufacturer','Category','Era','Core status']); self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.itemSelectionChanged.connect(self.show_details); self.table.cellChanged.connect(self.cell_changed); self.table.horizontalHeader().setStretchLastSection(True); root.addWidget(self.table)
        bottom=QHBoxLayout(); self.details=QTextEdit(); self.details.setReadOnly(True); self.details.setMaximumHeight(135); bottom.addWidget(self.details)
        actions=QVBoxLayout(); self.selectall=QPushButton('Select all filtered'); self.selectall.clicked.connect(self.select_all); clear=QPushButton('Clear selection'); clear.clicked.connect(self.clear_selection); fav=QPushButton('Pin selected'); fav.clicked.connect(self.pin_selected); add=QPushButton('Add selected systems'); add.clicked.connect(self.accept_selected); actions.addWidget(self.selectall);actions.addWidget(clear);actions.addWidget(fav);actions.addWidget(add);bottom.addLayout(actions);root.addLayout(bottom)
    def refresh_cores(self):
        exe=self.db.conn.execute("SELECT executable FROM emulator_definitions WHERE name='RetroArch'").fetchone(); self.cores=discover_cores(exe['executable'] if exe else '')
        with self.db.conn:
            for c in self.cores:self.db.conn.execute('INSERT OR REPLACE INTO core_metadata(library_path,display_name,version,systems,extensions,status,discovered_at) VALUES(?,?,?,?,?,?,strftime(\'%s\',\'now\'))',(c['library_path'],c['name'],c.get('version',''),c.get('systems',''),c.get('extensions',''),c['status']))
    def rows(self):
        rows=search_catalog(self.search.text(), '' if self.category.currentText()=='All categories' else self.category.currentText())
        enabled={r['system_id'] for r in self.db.conn.execute('SELECT system_id FROM enabled_systems WHERE enabled=1')}; self.favorites={r['system_id'] for r in self.db.conn.execute('SELECT system_id FROM enabled_systems WHERE favorite=1')}
        def status(s): return 'Installed' if any(core_matches(s,c) for c in self.cores) else ('Experimental' if not s.verified else 'Missing core')
        if self.installed.isChecked(): rows=[s for s in rows if status(s)=='Installed']
        key={'Name':lambda s:s.name.casefold(),'Manufacturer':lambda s:s.manufacturer.casefold(),'Category':lambda s:s.category.casefold(),'Installation status':lambda s:status(s)}[self.sort.currentText()]
        return sorted(rows,key=key),enabled,status
    def refresh(self):
        rows,enabled,status=self.rows(); self.table.blockSignals(True); self.table.setRowCount(0)
        for s in rows:
            r=self.table.rowCount(); self.table.insertRow(r); check=QTableWidgetItem(); check.setFlags(Qt.ItemIsEnabled|Qt.ItemIsUserCheckable); check.setCheckState(Qt.Checked if s.system_id in self.selected else Qt.Unchecked); check.setData(Qt.UserRole,s.system_id); self.table.setItem(r,0,check)
            vals=[s.name,s.manufacturer,s.category,s.era,status(s)];
            for c,v in enumerate(vals,1):self.table.setItem(r,c,QTableWidgetItem(v))
            self.table.item(r,1).setData(Qt.UserRole,s.system_id)
            if s.system_id in enabled:self.table.item(r,1).setText('✓ '+s.name)
        self.table.blockSignals(False)
    def cell_changed(self,row,col):
        if col==0:
            sid=self.table.item(row,0).data(Qt.UserRole)
            if self.table.item(row,0).checkState()==Qt.Checked:self.selected.add(sid)
            else:self.selected.discard(sid)
    def select_all(self):
        for r in range(self.table.rowCount()): self.selected.add(self.table.item(r,0).data(Qt.UserRole)); self.table.item(r,0).setCheckState(Qt.Checked)
    def clear_selection(self):
        self.selected.clear(); self.refresh()
    def pin_selected(self):
        with self.db.conn:
            for sid in self.selected:self.db.conn.execute('INSERT INTO enabled_systems(system_id,favorite,created_at) VALUES(?,?,strftime(\'%s\',\'now\')) ON CONFLICT(system_id) DO UPDATE SET favorite=1',(sid,1))
        self.refresh()
    def show_details(self):
        r=self.table.currentRow()
        if r<0:return
        sid=self.table.item(r,1).data(Qt.UserRole); s=next((x for x in CATALOG if x.system_id==sid),None)
        if not s:return
        matches=[c for c in self.cores if core_matches(s,c)]; lines=[f'{s.name}  •  {s.manufacturer}  •  {s.era}',f'Category: {s.category}',f'Aliases: {", ".join(s.aliases)}',f'ROM extensions: {", ".join(s.extensions)}',f'Compatible detected cores ({len(matches)}):']
        lines += [f"  {'✓' if Path(c['library_path']).is_file() else '✗'} {c['name']} — {c['library_path']}" for c in matches] or ['  No compatible installed core detected.']
        if s.notes:lines.append('Note: '+s.notes)
        self.details.setPlainText('\n'.join(lines))
    def accept_selected(self):
        if not self.selected: QMessageBox.information(self,'No systems selected','Select one or more systems first.'); return
        _,enabled,_=self.rows()
        with self.db.conn:
            for sid in self.selected:
                s=next(x for x in CATALOG if x.system_id==sid)
                self.db.conn.execute('INSERT INTO enabled_systems(system_id,created_at) VALUES(?,strftime(\'%s\',\'now\')) ON CONFLICT(system_id) DO UPDATE SET enabled=1',(sid,))
                self.db.conn.execute('INSERT OR IGNORE INTO systems(name,extensions,emulator) VALUES(?,?,?)',(s.name,','.join(s.extensions),'RetroArch'))
                for c in self.cores:
                    if core_matches(s,c): self.db.conn.execute('INSERT OR IGNORE INTO system_core_mappings(system_id,library_path) VALUES(?,?)',(sid,c['library_path']))
        self.accept()
