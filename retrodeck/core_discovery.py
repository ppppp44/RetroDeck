from __future__ import annotations
from pathlib import Path
from .catalog import CATALOG
DEFAULT_CORE_DIRS=[Path.home()/'.config/retroarch/cores',Path.home()/'.local/share/retroarch/cores',Path('/usr/lib/libretro'),Path('/usr/lib/x86_64-linux-gnu/libretro'),Path.home()/'.var/app/org.libretro.RetroArch/config/retroarch/cores']
if __import__('os').name=='nt':
    _appdata=Path(__import__('os').environ.get('APPDATA',Path.home()/'AppData/Roaming'))
    DEFAULT_CORE_DIRS=[_appdata/'RetroArch/cores',Path.home()/'scoop/apps/retroarch/current/cores']
def discover_core_dirs(retroarch_executable=''):
    dirs=[]; exe=Path(retroarch_executable).expanduser() if retroarch_executable else None
    candidates=[]
    if exe: candidates += [exe.parent/'cores',exe.parent.parent/'cores',exe.parent/'../share/retroarch/cores']
    for cfg in [Path.home()/'.config/retroarch/retroarch.cfg']:
        if cfg.is_file():
            for line in cfg.read_text(errors='ignore').splitlines():
                if line.strip().startswith('libretro_directory'):
                    candidates.insert(0,Path(line.split('=',1)[1].strip().strip('"')).expanduser())
    for p in candidates+DEFAULT_CORE_DIRS:
        p=Path(p).expanduser()
        if p.is_dir() and p not in dirs: dirs.append(p)
    return dirs
def _info(path):
    info=path.with_suffix('.info')
    if not info.is_file(): return {}
    data={}
    for line in info.read_text(errors='ignore').splitlines():
        if '=' in line:
            k,v=line.split('=',1); data[k.strip()]=v.strip().strip('"')
    return data
def discover_cores(retroarch_executable=''):
    found=[]; seen=set()
    for root in discover_core_dirs(retroarch_executable):
        patterns=('*_libretro.dll','*_libretro.so') if __import__('os').name=='nt' else ('*_libretro.so',)
        paths=[]
        for pattern in patterns: paths += list(root.glob(pattern))
        for path in sorted(paths):
            if path in seen or not path.is_file(): continue
            seen.add(path); meta=_info(path); name=meta.get('display_name') or path.stem.replace('_libretro','').replace('_',' ').title()
            found.append({'name':name,'library_path':str(path.resolve()),'extensions':meta.get('supported_extensions','').replace('|',','),'systems':meta.get('corename',name),'version':meta.get('version',''),'status':'available','info':meta})
    return found
def core_matches(system, core):
    hay=' '.join((core.get('name',''),core.get('systems',''),core.get('extensions',''))).casefold()
    return any(x.casefold() in hay for x in (system.name,system.system_id,*system.aliases,*system.core_hints))
