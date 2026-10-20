# RetroDeck 0.5.1 — Windows Installation Guide

RetroDeck is a native Windows game-library frontend for organizing ROM folders, configuring emulators, scanning games, and launching them from one interface.

RetroDeck does not bundle emulators, BIOS files, encryption keys, ROMs, or other copyrighted game components. Install and configure those components separately from their official sources.

## Option 1: Install the packaged Windows release

The Windows release is distributed as a folder containing `RetroDeck.exe` and its runtime files, or as a ZIP archive named similar to:

```
RetroDeck-0.5.1-windows.zip
```

1. Download the Windows ZIP release.

1. Right-click the ZIP file, choose **Properties**, and select **Unblock** if that option is shown.

1. Extract the entire ZIP to a normal folder such as:

   ```
   C:\Games\RetroDeck
   ```

1. Open the extracted `RetroDeck` folder.

1. Double-click `RetroDeck.exe`.

Keep the complete extracted folder together. Do not copy only the EXE because the PySide6 runtime and bundled audio assets are stored beside it.

If Windows Defender SmartScreen appears for a locally built or unsigned release, verify that the file came from your trusted release source before choosing **More info → Run anyway**. Do not bypass warnings for an unknown download.

## Option 2: Build the Windows release yourself

Build on Windows 10 or Windows 11 with Python 3.10 or newer.

1. Install Python from [python.org](https://www.python.org/downloads/windows/). During setup, enable **Add Python to PATH**.

1. Open PowerShell.

1. Clone or extract the RetroDeck source tree.

1. Change to the project directory:

   ```
   cd C:\Path\To\retrodeck
   ```

1. Run the reproducible build script:

   ```
   .\build\build-windows.ps1
   ```

The script installs the Windows build dependencies, runs PyInstaller, copies the application assets, and creates:

```
dist\RetroDeck\RetroDeck.exe
dist\RetroDeck-0.5.1-windows.zip
```

To run the same build through GitHub Actions, use the workflow at:

```
.github\workflows\windows-release.yml
```

It runs on a Windows runner and uploads the executable folder and ZIP as build artifacts.

## First launch

On first launch, RetroDeck creates its Windows user data under:

```
%APPDATA%\RetroDeck
```

The setup wizard will guide you through:

1. Selecting the systems you use.

1. Selecting one or more ROM folders or additional drives.

1. Detecting installed emulators.

1. Choosing an emulator or RetroArch core for each system.

1. Reviewing the configuration.

1. Running the initial scan.

RetroDeck only scans folders you select. It does not assume that your Windows ROM folders match a Linux installation.

If detection does not find an emulator, select **Settings → Browse** and choose the emulator executable manually.

## Emulator configuration

RetroDeck supports Windows installations of:

- Cemu

- Dolphin

- RPCS3

- Ryujinx

- RetroArch and installed cores

- Other manually configured standalone emulators

Open **Settings** to edit the following values for each emulator:

- Executable path, such as `C:\Emulators\RPCS3\rpcs3.exe`

- Working directory

- Additional command-line arguments

- Launch method

Paths containing spaces are supported. Do not enter Linux paths such as `/data/...` or Linux AppImage filenames in the Windows configuration.

RetroArch cores are discovered as Windows `.dll` files in common RetroArch core folders. You can also add or edit a core manually from the RetroArch Core Manager.

## Library scanning

Use **Systems → Add folder** to assign a ROM folder to a system. You can add multiple folders and drives. Then choose **Scan selected** or use the global scan action.

The scanner:

- Recurses through selected folders.

- Avoids common development and system folders.

- Does not modify ROM files.

- Keeps unavailable folders in the database.

- Marks games as missing if a drive is disconnected.

- Supports pause, resume, and cancel.

## Controller support

RetroDeck supports Linux joystick devices directly and provides keyboard navigation on every platform. On Windows, controller input depends on the controller being exposed through a compatible joystick interface by Windows and its driver.

The keyboard fallback is always available:

- Arrow keys: navigate

- Enter: accept or launch

- Escape: return Home

Mouse navigation remains available as well.

## Music and interface audio

The sidebar provides:

- Ambient music on/off

- Ambient volume control

- Short confirmation feedback for navigation and launch actions

Audio settings are stored in the RetroDeck SQLite database and persist between launches.

## Existing databases and upgrades

RetroDeck upgrades SQLite databases additively. It does not delete or recreate an existing library.

For a safe migration from an earlier installation:

1. Close the older RetroDeck application.

1. Make a backup of the existing database.

1. Copy the database to the Windows RetroDeck data location only if you intentionally want to migrate it:

   ```
   %APPDATA%\RetroDeck\library.sqlite3
   ```

1. Start the Windows edition.

1. Review emulator paths in **Settings** because Linux executable paths are not valid on Windows.

1. Re-select Windows ROM folders and Windows emulator executables if necessary.

The database preserves games, favorites, system definitions, setup state, and other compatible settings. Windows-specific paths must be configured separately; RetroDeck never launches Linux AppImages from the Windows adapter.

Before a major migration, use **Settings → Back up database** and keep the backup outside the active data folder.

## Resetting only the Windows configuration

To preserve the existing database, do not delete the RetroDeck data folder. Use the in-app backup, restore, and setup-wizard controls instead.

If you intentionally need a fresh Windows setup, close RetroDeck and rename the data folder:

```
%APPDATA%\RetroDeck
```

to something such as:

```
%APPDATA%\RetroDeck-backup
```

Starting RetroDeck afterward creates a new database. Keep the renamed folder until you confirm that the new installation works.

## Troubleshooting

### RetroDeck.exe does not start

Confirm that you extracted the complete release folder rather than copying only the EXE. If you built from source, rerun the PowerShell build script from the project root.

### An emulator is shown as missing

Open **Settings**, use **Browse**, and select the actual Windows executable. Do not rely on a guessed installation path.

### A game is missing

Check whether its drive is mounted and whether the selected ROM folder still exists. Re-add the folder if its drive letter changed, then scan again.

### A game does not launch

Verify the emulator executable, working directory, command-line arguments, and RetroArch core mapping. Paths with spaces are supported, but the executable and game file must both exist.

### Windows cannot access the ROM folder

Check the folder permissions and confirm that the user running RetroDeck can read the folder. Avoid selecting protected system directories.

## Data and privacy

RetroDeck stores its library database and local preferences under `%APPDATA%\RetroDeck`. It does not upload ROM files, bundle games, or download restricted emulator components automatically.
