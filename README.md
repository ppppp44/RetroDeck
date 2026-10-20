# RetroDeck Infinity 0.5.1

RetroDeck is a lightweight native Linux emulation frontend. It keeps an independent SQLite library under `~/.local/share/retrodeck/library.sqlite3`, never copies ROMs, and does not download artwork or alter existing emulator configuration.

## Install

Build the package with `./build/build-deb.sh`, then install it on Ubuntu/Mint with:

```bash
sudo apt install ./build/retrodeck_0.5.0_amd64.deb
```

The package requires Python 3 and uses the existing PySide6 installation; it deliberately does not depend on the unavailable `python3-pyside6` APT package. Verify it with `python3 -c "import PySide6; print(PySide6.__version__)"`. Launch with `retrodeck` or from the Applications menu. Remove with `sudo apt remove retrodeck`; user data is intentionally preserved.

## First run and configuration

The **Home** screen reports actual indexed counts, mounted volumes, and targeted emulator detection. Open **Settings** to browse for Cemu, Dolphin, PCSX2 and RetroArch executables, re-detect installations, or back up/restore the SQLite database. The requested defaults are pre-populated but remain editable. Open **Systems → Universal System Picker** to add catalog systems, then **Add folder** to add any number of roots per system. Add each mounted partition separately, then use **Scan selected** or **Rescan enabled folders**. Scanning is recursive, skips common development folders, avoids symlink loops, supports pause/resume/cancel, and retains missing-drive entries as unavailable.

Double-click a library row to launch. PCSX2 uses `APPIMAGE -- game`; Cemu uses `APPIMAGE -g game`; Dolphin uses `APPIMAGE game`; RetroArch uses `APPIMAGE -L core.so game`. RetroArch core mappings can be added in the database/UI extension point; games without an unambiguous core are rejected rather than silently routed to an unrelated core.

## Testing

Run the standard-library tests from the source directory:

```bash
python3 -m unittest discover -s tests -v
```

Actual user AppImages and ROM partitions are not present in this build sandbox, so emulator startup against those exact paths remains unverified. The tests cover database migration, multiple roots, recursive scanning, duplicate paths, missing files, safe argument construction, mount discovery, backup/restore, scan controls, ZIP inspection, and paths containing spaces/punctuation. The final package structure can be inspected with `dpkg-deb -c build/retrodeck_0.5.0_amd64.deb`.

## Troubleshooting

If a drive is unavailable, the folder remains configured and indexed games are marked Missing until the drive is mounted and rescanned. If an emulator is missing or not executable, choose a replacement in Settings. If RetroArch says no core is mapped, configure the core assignment before launching. Unsupported extensions are ignored by the scanner. BIOS, invalid images, and emulator-specific errors are reported by the emulator and are not silently treated as frontend failures.

Installed size is the small application/package footprint; the SQLite database and all ROMs remain in their original user locations and are not included in the package.

## Universal System Picker

The Systems tab now includes a searchable Universal System Picker containing 104 stable-ID catalog entries across Nintendo, Sony, Sega, Atari, NEC, SNK, computers, DOS, arcade, and other platforms. Filter by category or installed-core status, sort by name/manufacturer/category/status, select multiple systems, pin systems, and review aliases, extensions, notes, and detected compatible cores before adding them.

RetroArch cores are discovered from the configured RetroArch directory, RetroArch configuration, AppImage-adjacent locations, Flatpak locations, and common Linux directories. Core `.info` metadata is used when present. Missing cores are shown as Missing core or Experimental; RetroDeck does not download or execute arbitrary binaries. Existing Dolphin, PCSX2, and Cemu integrations remain separate and unchanged.

Upgrade an existing installation with `sudo apt install ./build/retrodeck_0.5.0_amd64.deb`. The migration is additive and preserves existing games, favorites, emulator paths, and directory settings.

## First-launch setup wizard

On a fresh data directory, RetroDeck opens a five-step setup wizard before the Home screen. Choose only the systems you own, assign one or more verified game folders to each system, select a detected RetroArch core or standalone emulator where available, review the configuration, and finish. The selected folders are written to the existing scan configuration and the real background scanner starts after the wizard closes. A system may intentionally remain in **Configure later** mode and will be marked as needing emulator setup rather than being presented as playable.

The wizard never modifies ROM files. Folder suggestions come only from accessible likely game directories on discovered mounted volumes. Existing setup state is stored in SQLite, so the wizard does not reappear on subsequent launches. To deliberately run it again, use **Settings → Run setup wizard again**; this merges selected systems and paths and does not reset the library. Use **Back up database** before major configuration changes if desired.

## Infinity visual redesign

The 0.5.0 interface uses a persistent navigation rail, cinematic hero panel, restrained indigo/violet/cyan lighting, metric cards backed by real SQLite and mount data, and higher-contrast library and settings surfaces. The composition takes inspiration from modern game launchers that put a focused library and clear per-game actions first, including the publicly visible VaultLauncher emphasis on organized game details and purposeful action sections. No VaultLauncher artwork, logos, or proprietary assets are included.

The Game Vault now has a **Box View** that gives every indexed game its own fixed 3D-styled neon case with system badge, title, format, availability state, and a working Play action. It intentionally uses geometric placeholder design rather than downloaded cover art. The sidebar includes an ambient music toggle and volume slider. The package carries an original looping synthwave ambience track and a short UI confirmation tone; audio can be muted and the setting persists locally.

Controller support is built in without requiring Python gamepad packages. Linux joystick devices under `/dev/input/js*` are read when permissions allow, with axis navigation, accept, back, menu, and next actions. Arrow keys, Enter, and Escape provide the same controller-style navigation fallback. A machine without a connected controller continues to work normally with mouse and keyboard.

SQLite upgrades are additive and backward-compatible. The application preserves existing games, paths, favorites, emulator definitions, and settings, creates missing tables, repairs missing columns from early builds, and records schema version 4 through SQLite `user_version`. It does not delete or recreate an older library database.

## Native Windows edition

RetroDeck 0.5.1 includes a native Windows build path that reuses the PySide6 frontend, scanner, catalog, setup wizard, library, and SQLite migrations. Windows data is stored under `%APPDATA%\RetroDeck`, while Linux continues to use `$XDG_DATA_HOME/retrodeck` or `~/.local/share/retrodeck`.

Windows discovery checks logical drives and common user/program locations for Cemu, Dolphin, RPCS3, Ryujinx, RetroArch, and RetroArch cores. Every emulator remains manually configurable through Settings. Windows launch commands use a dedicated adapter with Windows quoting and working-directory rules; Linux AppImage paths and Linux process assumptions are not used by the Windows adapter. Emulator arguments, working directory, and launch method are editable in Settings.

Build the actual Windows executable on Windows PowerShell with Python and PySide6 installed:

```powershell
.\build\build-windows.ps1
```

That command produces `dist\RetroDeck\RetroDeck.exe` and `dist\RetroDeck-0.5.1-windows.zip`. A GitHub Actions workflow is also provided at `.github\workflows\windows-release.yml` and runs on `windows-latest`, including a packaged-launch smoke test. This sandbox is Linux and has no Windows runner, so the Windows executable and Windows screenshots must be produced by that Windows runner rather than being falsely represented by the Linux `.deb`.
