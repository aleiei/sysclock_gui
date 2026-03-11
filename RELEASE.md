# SYSCLOCK v1.0.4

Release date: 2026-03-11

## Highlights

- Added Linux standalone executables to `dist/`.
- Updated `README.md` (both Italian and English sections) with dedicated **Linux standalone** section.
- Added launch instructions for `dist/sysclock_gui` (Dark) and `dist/sysclock_gui_clear` (Clear).
- Updated Quick Launch Reference tables to include both Linux standalone variants.

## Assets

| File | Description |
|---|---|
| `dist/sysclock_gui` | Linux standalone — Dark version |
| `dist/sysclock_gui_clear` | Linux standalone — Clear version |
| `dist/SysClockControl.exe` | Windows 11 standalone |

## Notes

- This is a documentation and distribution release.
- No runtime code changes in `sysclock_gui.py` or `sysclock_gui_clear.py`.
- Linux executables built with PyInstaller (`-F -w`).

## Linux Build Commands

```bash
pip install pyinstaller
pyinstaller -F -w --name sysclock_gui sysclock_gui.py
pyinstaller -F -w --name sysclock_gui_clear sysclock_gui_clear.py
```

## GitHub Release Metadata

- Tag: `v1.0.4`
- Release title: `SYSCLOCK v1.0.4`
