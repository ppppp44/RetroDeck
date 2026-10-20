# Build on Windows with: pyinstaller --clean --noconfirm packaging/RetroDeck.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

root=Path.cwd()
hiddenimports=collect_submodules('PySide6.QtMultimedia')
a=Analysis(['retrodeck/__main__.py'], pathex=[str(root)], binaries=[], datas=[(str(root/'assets'),'assets')], hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz=PYZ(a.pure)
exe=EXE(pyz,a.scripts,cipher=None,name='RetroDeck',debug=False,strip=False,upx=True,console=False,icon=str(root/'assets/retrodeck.ico') if (root/'assets/retrodeck.ico').exists() else None)
coll=COLLECT(exe,a.binaries,a.datas,a.zipfiles,name='RetroDeck')
