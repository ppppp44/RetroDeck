from __future__ import annotations
import os, shutil
from pathlib import Path
from .core_discovery import discover_cores, discover_core_dirs
if os.name == 'nt':
    from .windows_platform import mounted_volumes_windows, likely_roots_windows, discover_windows_emulators

VIRTUAL_FS={'proc','sysfs','devtmpfs','devpts','tmpfs','cgroup','cgroup2','overlay','squashfs','pstore','securityfs','debugfs','tracefs','fusectl','configfs','ramfs','hugetlbfs','mqueue','autofs'}
SKIP_MOUNTS={Path('/proc'),Path('/sys'),Path('/dev'),Path('/run'),Path('/tmp')}
def mounted_volumes():
    if os.name == 'nt': return mounted_volumes_windows()
    result=[]; seen=set()
    try: lines=Path('/proc/self/mountinfo').read_text(errors='replace').splitlines()
    except OSError: return result
    for line in lines:
        try:
            left,right=line.split(' - ',1); parts=left.split(); mount=Path(parts[4].replace('\\040',' ').replace('\\011','\t')); fs=right.split()[0]; source=right.split()[1] if len(right.split())>1 else ''
            if fs in VIRTUAL_FS or mount in SKIP_MOUNTS or not mount.is_dir() or mount in seen: continue
            if str(mount).startswith(('/proc/','/sys/','/dev/','/run/')): continue
            seen.add(mount); result.append({'path':str(mount),'filesystem':fs,'source':source,'accessible':os.access(mount,os.R_OK|os.X_OK),'free_bytes':shutil.disk_usage(mount).free if os.access(mount,os.R_OK) else None})
        except (ValueError,OSError,IndexError): continue
    return sorted(result,key=lambda x:x['path'])
def likely_roots(volumes=None):
    if os.name == 'nt': return likely_roots_windows(volumes)
    volumes=volumes if volumes is not None else mounted_volumes(); roots=[]
    candidates=[Path.home()/'Games',Path.home()/'ROMs',Path.home()/'Roms',Path.home()/'Emulation',Path.home()/'Documents/Games']
    for v in volumes: candidates += [Path(v['path'])/'Games',Path(v['path'])/'ROMs',Path(v['path'])/'Roms',Path(v['path'])/'Emulation']
    for p in candidates:
        try:
            if p.is_dir() and p not in roots:
                roots.append(p)
        except OSError:
            continue
    return roots
def discover_emulators(retroarch_executable=''):
    if os.name == 'nt':
        result=discover_windows_emulators()
        if retroarch_executable and not any(x['path'].lower()==retroarch_executable.lower() for x in result): result.append({'name':'RetroArch','path':retroarch_executable,'available':Path(retroarch_executable).is_file(),'type':'frontend'})
        return result
    candidates={'RetroArch':[], 'Cemu':[], 'Dolphin':[], 'PCSX2':[]}
    for name in candidates:
        for command in ([name.lower(),name] if name!='RetroArch' else ['retroarch']):
            found=shutil.which(command)
            if found and found not in candidates[name]: candidates[name].append(found)
    candidates['RetroArch'] += [retroarch_executable] if retroarch_executable else []
    common={'Cemu':['/data/Cemu-2.6-x86_64.AppImage'],'Dolphin':['/data/Dolphin_Emulator-2606a-anylinux-x86_64.AppImage'],'PCSX2':['/data/pcsx2-v2.8.2-linux-appimage-x64-Qt.AppImage']}
    for name,paths in common.items():
        for p in paths:
            if p not in candidates[name]: candidates[name].append(p)
    return [{'name':n,'path':p,'available':Path(p).is_file() and os.access(p,os.X_OK),'type':'standalone' if n!='RetroArch' else 'frontend'} for n,paths in candidates.items() for p in paths]
