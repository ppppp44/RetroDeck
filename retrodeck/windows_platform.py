from __future__ import annotations
import os
from pathlib import Path

WINDOWS_EMULATORS={
    'Cemu': ['Cemu.exe'],
    'Dolphin': ['Dolphin.exe','DolphinQt.exe'],
    'RPCS3': ['rpcs3.exe'],
    'Ryujinx': ['Ryujinx.exe','Ryujinx.Ava.exe'],
    'RetroArch': ['retroarch.exe'],
}

def logical_drives():
    if os.name != 'nt': return []
    drives=[]
    for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        p=Path(f'{letter}:/')
        if p.exists(): drives.append(p)
    return drives

def mounted_volumes_windows():
    result=[]
    for p in logical_drives():
        try:
            result.append({'path':str(p),'filesystem':'Windows volume','source':str(p),'accessible':os.access(p,os.R_OK|os.X_OK),'free_bytes':None})
        except OSError: pass
    return result

def likely_roots_windows(volumes=None):
    volumes=volumes if volumes is not None else mounted_volumes_windows(); roots=[]
    candidates=[Path.home()/'Games',Path.home()/'ROMs',Path.home()/'Roms',Path.home()/'Emulation',Path.home()/'Documents/Games',Path.home()/'Documents/ROMs']
    for volume in volumes:
        p=Path(volume['path']); candidates += [p/'Games',p/'ROMs',p/'Roms',p/'Emulation']
    for p in candidates:
        if p.is_dir() and p not in roots: roots.append(p)
    return roots

def _common_roots():
    roots=[]
    for env in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA','APPDATA'):
        value=os.environ.get(env)
        if value: roots.append(Path(value))
    roots += [Path.home()/'scoop/apps',Path.home()/'Desktop']
    return roots

def discover_windows_emulators():
    found=[]; seen=set()
    for name,filenames in WINDOWS_EMULATORS.items():
        for filename in filenames:
            candidates=[]
            path=os.environ.get(f'RETRODECK_{name.upper()}_EXE')
            if path: candidates.append(Path(path))
            for root in _common_roots():
                candidates += list(root.glob(f'**/{filename}')) if root.is_dir() else []
            for candidate in candidates:
                key=str(candidate).lower()
                if key in seen: continue
                seen.add(key); found.append({'name':name,'path':str(candidate),'available':candidate.is_file(),'type':'frontend' if name=='RetroArch' else 'standalone'})
    return found
