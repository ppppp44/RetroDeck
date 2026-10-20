from __future__ import annotations
from pathlib import Path
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect
import os

class AudioManager:
    def __init__(self, asset_dir: str | Path, enabled=True, volume=0.24):
        self.asset_dir=Path(asset_dir); self.enabled=enabled; self.volume=float(volume); self.headless=os.environ.get('QT_QPA_PLATFORM','').lower() in {'offscreen','minimal'}
        self.music_player=None; self.music_output=None; self.confirm=None
        music=self.asset_dir/'retrodeck-ambience.wav'
        if not music.exists(): music=self.asset_dir/'retrodeck-ambience.mp3'
        self.music_path=music
        if not self.headless:
            self.music_player=QMediaPlayer(); self.music_output=QAudioOutput(); self.music_player.setAudioOutput(self.music_output); self.music_output.setVolume(self.volume); self.music_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.confirm=QSoundEffect(); self.confirm.setSource(QUrl.fromLocalFile(str(self.asset_dir/'retrodeck-ui-confirm.wav'))); self.confirm.setVolume(min(1.0,self.volume*2.5))
            if music.exists(): self.music_player.setSource(QUrl.fromLocalFile(str(music)))
    def play_music(self):
        if self.enabled and self.music_player and self.music_path.exists(): self.music_player.play()
    def stop_music(self):
        if self.music_player: self.music_player.stop()
    def set_volume(self,value):
        self.volume=max(0.0,min(1.0,float(value)))
        if self.music_output: self.music_output.setVolume(self.volume)
        if self.confirm: self.confirm.setVolume(min(1.0,self.volume*2.5))
    def toggle(self):
        self.enabled=not self.enabled
        if self.enabled:self.play_music()
        else:self.stop_music()
        return self.enabled
    def play_confirm(self):
        if self.enabled and self.confirm and self.confirm.source().isValid(): self.confirm.play()
    def close(self):
        if self.music_player: self.music_player.stop()
