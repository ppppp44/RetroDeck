from __future__ import annotations
import os, shlex, subprocess
from pathlib import Path

class LaunchValidationError(ValueError): pass

class BaseProcessAdapter:
    platform='generic'
    def validate(self, emulator, game, core=None):
        exe=Path(emulator['executable']).expanduser(); game_path=Path(game['path']).expanduser()
        if not exe.is_file(): raise LaunchValidationError(f'Emulator executable not found: {exe}')
        if not game_path.is_file(): raise LaunchValidationError(f'Game file not found: {game_path}')
        return exe, game_path
    def extra_args(self, emulator, extra):
        raw=extra or (emulator['default_args'] if 'default_args' in emulator.keys() else '')
        return shlex.split(raw, posix=self.platform!='windows') if raw else []

class LinuxProcessAdapter(BaseProcessAdapter):
    platform='linux'
    def command(self, emulator, game, core=None, extra='', validate_paths=True):
        exe,path=self.validate(emulator,game,core) if validate_paths else (Path(emulator['executable']).expanduser(),Path(game['path']).expanduser()); name=emulator['name']
        if name=='RetroArch':
            if not core: raise LaunchValidationError('No RetroArch core is mapped to this game.')
            args=[str(exe),'-L',str(core),str(path)]
        elif name=='PCSX2': args=[str(exe),'--',str(path)]
        elif name=='Cemu': args=[str(exe),'-g',str(path)]
        else: args=[str(exe),str(path)]
        return args+self.extra_args(emulator,extra)

class WindowsProcessAdapter(BaseProcessAdapter):
    platform='windows'
    def command(self, emulator, game, core=None, extra='', validate_paths=True):
        exe,path=self.validate(emulator,game,core) if validate_paths else (Path(emulator['executable']).expanduser(),Path(game['path']).expanduser()); name=emulator['name']
        if name=='RetroArch':
            if not core: raise LaunchValidationError('No RetroArch core is mapped to this game.')
            args=[str(exe),'-L',str(core),str(path)]
        elif name=='Cemu': args=[str(exe),'-g',str(path)]
        elif name in ('RPCS3','Ryujinx','Dolphin'): args=[str(exe),str(path)]
        else: args=[str(exe),str(path)]
        return args+self.extra_args(emulator,extra)
    def working_directory(self, emulator, game):
        configured=emulator['working_directory'] if 'working_directory' in emulator.keys() else ''
        return str(Path(configured).expanduser()) if configured else str(Path(emulator['executable']).parent)

def adapter_for_platform():
    return WindowsProcessAdapter() if os.name=='nt' else LinuxProcessAdapter()

def spawn(adapter, emulator, game, core=None, extra=''):
    command=adapter.command(emulator,game,core,extra,validate_paths=True)
    working=(adapter.working_directory(emulator,game) if hasattr(adapter,'working_directory') else (emulator['working_directory'] if 'working_directory' in emulator.keys() and emulator['working_directory'] else str(Path(game['path']).parent)))
    return subprocess.Popen(command, shell=False, cwd=working, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True), command
