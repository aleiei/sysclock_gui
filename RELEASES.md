# RELEASES

## v1.0.4 - 2026-03-11

Distribution update: Linux standalone executables added.

### Included

- Added `dist/sysclock_gui` — Linux standalone executable, Dark version (PyInstaller).
- Added `dist/sysclock_gui_clear` — Linux standalone executable, Clear version (PyInstaller).
- Updated `README.md` (IT + EN) with dedicated Linux standalone section and launch instructions.
- Updated Quick Launch Reference tables with `dist/sysclock_gui` and `dist/sysclock_gui_clear` entries.
- Updated `README.md` current version badge to `v1.0.4`.

### Repository Metadata

- Tag: `v1.0.4`
- GitHub release: `SYSCLOCK v1.0.4`
- Main assets: `dist/sysclock_gui`, `dist/sysclock_gui_clear`

### Linux Build Commands

```bash
pyinstaller -F -w --name sysclock_gui sysclock_gui.py
pyinstaller -F -w --name sysclock_gui_clear sysclock_gui_clear.py
```

---

## v1.0.3 - 2026-03-10

Documentation update focused on screenshot placement and readability.

### Included

- Updated `README.md` current version badge to `v1.0.3`.
- Expanded screenshot section to include both `images/1.png` and `images/2.png`.
- Added contextual screenshot references near the FT8/FT4 operational panel sections (Italian and English).

### Repository Metadata

- Tag: `v1.0.3`
- GitHub release: `SYSCLOCK v1.0.3`

## v1.0.2 - 2026-03-10

Release dedicated to the Windows standalone executable package.

### Included

- Added and validated standalone build target for `SysClockControl.exe` (Windows 11).
- Updated release focus to provide a Python-free execution path for Windows users.
- Confirmed administrator launch requirement for all system time operations.

### Repository Metadata

- Tag: `v1.0.2`
- GitHub release: `SYSCLOCK v1.0.2`
- Main asset: `SysClockControl.exe`

### Windows Build Command

```cmd
python -m PyInstaller -F -w --name SysClockControl sysclock_gui.py
```

## v1.0.1 - 2026-03-09

Patch release focused on repository presentation and documentation clarity.

### Included

- Added a project screenshot section at the top of `README.md`.
- Linked image asset (`images/1.png`) in README for immediate UI preview.
- Minor documentation context improvements for project landing section.

### Repository Metadata

- Tag: `v1.0.1`
- GitHub release: `SYSCLOCK v1.0.1`

### Quick Run

```bash
sudo python3 sysclock_gui.py
```

## v1.0.0 - 2026-03-08

First public release of **SYSCLOCK**.

### Included

- Desktop GUI application written in Python 3 using tkinter.
- System clock step forward/backward controls.
- Exact date/time set panel.
- NTP enable/disable controls.
- Timezone selection and apply.
- Offset history chart and operation log.
- Keyboard shortcuts for quick control.

### Repository Metadata

- License: GNU GPL v3.0 (`LICENSE`)
- Tag: `v1.0.0`
- GitHub release: `SYSCLOCK v1.0.0`
- Topics: `python`, `tkinter`, `desktop-gui`, `system-clock`, `time-sync`, `ntp`, `timezone`, `clock-management`, `amateur-radio`, `ham-radio`, `ft8`, `ft4`, `wsjtx`, `jtdx`, `mshv`

### Quick Run

```bash
sudo python3 sysclock_gui.py
```
