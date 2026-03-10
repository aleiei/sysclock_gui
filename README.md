# SYSCLOCK — System Time Control

> **Ham Radio — Strumento per radioamatori / Ham Radio Tool**
> © 2026 Alessandro Orlando — GNU General Public License v3.0

> **Versione corrente / Current version: v1.0.3 (2026-03-10)**

---

## Screenshot

### Vista generale / General overview

![SYSCLOCK GUI overview](images/1.png)

### Pannelli operativi / Operational panels

![SYSCLOCK GUI operational panels](images/2.png)

---

## 🇮🇹 Italiano

### Descrizione

**SYSCLOCK — System Time Control** è un'applicazione desktop con interfaccia grafica (GUI) scritta interamente in **Python 3** usando la libreria standard **tkinter**, senza dipendenze esterne.

È pensata specificamente per i **radioamatori** che operano con i **modi digitali** (FT8, FT4, JT65, JT9 e simili), dove la precisione dell'orologio di sistema è critica. Consente di correggere rapidamente la sincronizzazione del clock direttamente dal valore **DT** riportato da WSJT-X, JTDX o MSHV, e di gestire NTP, fuso orario e ora esatta in un'unica interfaccia.

---

### Perché i radioamatori ne hanno bisogno

I modi digitali deboli come **FT8** e **FT4** si basano su slot temporali fissi di 15 secondi sincronizzati con UTC. Se l'orologio del computer devia anche solo di 1–2 secondi, le decodifiche falliscono e la trasmissione diventa impossibile. Il parametro **DT** (Delta Time) mostrato da WSJT-X, JTDX e MSHV indica esattamente questo scarto.

SYSCLOCK permette di:

- Correggere il clock del PC in un click inserendo il valore DT
- Operare **senza connessione internet** (operazioni portatili, contest, SOTA, POTA)
- Disabilitare NTP in modo completo per evitare che il demone reintroduca derive
- Impostare l'ora manualmente da un riferimento GPS o orologio atomico
- Monitorare visivamente la deriva accumulata nel tempo tramite il grafico storico

| Situazione | Come usare SYSCLOCK |
|---|---|
| DT mostrato in WSJT-X è ±0.5s o più | Inserire il valore DT nel pannello FT8 e premere **APPLY DT** |
| Operazione portatile senza internet | Disabilitare NTP, impostare l'ora con **SET EXACT TIME** da GPS |
| Deriva progressiva durante un contest | Monitorare il grafico storico e applicare correzioni DT al volo |
| NTP non disponibile o inaffidabile | Disabilitare NTP e usare **RESTORE CLOCK FROM SNAPSHOT** |
| Cambio fuso orario in trasferta | Aggiornare il SO con il pannello **TIMEZONE** in un click |

> **Compatibile con WSJT-X · JTDX · MSHV**

---

### Descrizione tecnica

| Voce | Dettaglio |
|---|---|
| Linguaggio | Python 3.8+ |
| GUI toolkit | tkinter (stdlib) + ttk |
| Dipendenze esterne | **Nessuna** |
| Sistemi operativi | Linux, macOS, Windows |
| Privilegi richiesti | root / amministratore per le operazioni di sistema |
| Architettura | Single-file, multi-thread con coda thread-safe (queue.Queue) |
| Licenza | GNU GPL v3.0 |

#### Funzioni attualmente in uso

| Funzione | Descrizione |
|---|---|
| `_linux_set_clock(dt)` | Imposta `CLOCK_REALTIME` via `clock_settime()` (libc, ns) + reset PLL con `adjtimex(2)` |
| `set_system_time(dt)` | Wrapper multi-OS: libc su Linux, `date` su macOS, `SetLocalTime` WinAPI su Windows |
| `ntp_enable()` | Unmask + riabilita tutti i demoni NTP noti tramite `timedatectl` e `systemctl` |
| `ntp_disable()` | Ferma, disabilita e **maschera** tutti i demoni NTP (incluso socket) + reset kernel PLL |
| `ntp_status()` | Verifica se NTP è attivo (`timedatectl` + `systemctl is-active` per ogni demone noto) |
| `get_timezones()` | Recupera l'elenco dei fusi orari (timedatectl / zoneinfo / tzutil) |
| `set_timezone(tz)` | Imposta il fuso orario di sistema (`timedatectl` / `systemsetup` / `tzutil`) |
| `RingBuffer` | Buffer circolare thread-safe per lo storico degli offset (120 campioni, ~2 min) |
| `SysClockApp` | Classe principale (tkinter.Tk), architettura producer/consumer con queue |
| `_do_step(ms)` | Calcola target da riferimento monotono e invia syscall al thread worker |
| `_tick()` | Loop principale (500ms): drena coda, aggiorna display, offset, history, chart |
| `_restore_clock()` | Ripristina l'ora OS dallo snapshot monotono — nessuna rete, nessun subprocess |

#### Costanti Linux

| Costante | Valore | Uso |
|---|---|---|
| `_NTP_UNITS` | 7 unit | Demoni e socket gestiti da `ntp_disable` / `ntp_enable` |
| `_CLOCK_REALTIME` | 0 | Clock ID per `clock_settime` |
| `_STA_UNSYNC` | 0x0040 | Segnala al kernel che il clock non è sincronizzato, blocca il PLL |
| `_ADJ_OFFSET/FREQUENCY/STATUS` | 0x0001/0x0002/0x0010 | Azzera offset, frequenza e stato PLL via `adjtimex` |

#### Comandi di sistema per OS

| OS | Operazione | Metodo |
|---|---|---|
| Linux | Imposta ora | `clock_settime(CLOCK_REALTIME)` via libc ctypes (nanosec) |
| Linux | Blocca deriva | `adjtimex(2)` reset PLL — struct Timex 208 byte |
| Linux | NTP disable | `timedatectl set-ntp false` + `systemctl stop/disable/mask` + reset PLL |
| Linux | NTP enable | `systemctl unmask` + `timedatectl set-ntp true` |
| Linux | Timezone | `timedatectl set-timezone` |
| macOS | Imposta ora | `date <MMDDHHmmYYYY.SS>` (sudo) |
| macOS | NTP | `systemsetup -setusingnetworktime on/off` |
| macOS | Timezone | `systemsetup -settimezone` |
| Windows | Imposta ora | `SetLocalTime()` WinAPI via ctypes (millisec) |
| Windows | NTP | `net start/stop w32time`, `w32tm /resync`, `sc config` |
| Windows | Timezone | `tzutil /s` |

---

### Funzionalità

- **Orologio live** — ora e data aggiornate ogni 500ms, calcolate da riferimento monotono (immune a derive OS)
- **FT8/FT4 DT Correction** — inserisci il DT da WSJT-X/JTDX/MSHV, correzione applicata con segno invertito; barra tolleranza visiva (verde < 0.5s, arancione < 1s, rosso ≥ 1s)
- **Pulsanti quick DT** — correzioni rapide ±0.1s, ±0.5s, ±1s, ±2s con un click
- **Imposta ora esatta** — data e ora manuali `YYYY-MM-DD / HH:MM:SS`, tasto **NOW** per precompilare
- **Gestione NTP completa** — ENABLE / DISABLE con mascheratura demoni; stato in tempo reale
- **Restore clock from snapshot** — ripristina l'ora precisa dallo snapshot del DISABLE NTP tramite contatore monotono (nessuna rete)
- **Gestione fuso orario** — menu a tendina con tutti i timezone, applicazione immediata
- **Grafico storico offset** — sparkline ultimi 2 minuti, thread-safe
- **Log operazioni** — registro timestampato, colori per esito
- **Compatibile Linux, macOS, Windows** — ogni OS usa le proprie API native

---

### Istruzioni d'uso

#### Installazione

##### 🐧 Linux

```bash
python3 --version
python3 -c "import tkinter; print('tkinter OK')"
# se tkinter manca:
sudo apt install python3-tk        # Debian/Ubuntu
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch

sudo python3 sysclock_gui.py
```

##### 🍎 macOS

```bash
brew install python3
python3 -c "import tkinter; print('tkinter OK')"
brew install python-tk   # se manca

sudo python3 sysclock_gui.py
```

##### 🪟 Windows

Installare Python 3.8+ da [python.org](https://www.python.org/downloads/windows/) con **"Add Python to PATH"** selezionato. Avviare da **Prompt come Amministratore**:

```cmd
cd C:\percorso\cartella
python sysclock_gui.py
```

##### 🪟 Windows 11 — Eseguibile standalone

È disponibile una versione precompilata compatibile con **Windows 11**, che non richiede l'installazione di Python.
Il file eseguibile si trova nella cartella `dist`:

```
dist\SysClockControl.exe
```

Per rigenerare l'eseguibile (maintainer release):

```cmd
python -m PyInstaller -F -w --name SysClockControl sysclock_gui.py
```

> **Importante:** avviare `SysClockControl.exe` con **click destro → Esegui come amministratore**, in quanto le operazioni di sistema richiedono privilegi elevati.

#### Riepilogo avvio

| Sistema | Comando |
|---|---|
| Linux | `sudo python3 sysclock_gui.py` |
| macOS | `sudo python3 sysclock_gui.py` |
| Windows | Prompt come Amministratore → `python sysclock_gui.py` |
| Windows 11 (standalone) | `dist\SysClockControl.exe` — click destro → **Esegui come amministratore** |

---

#### Pannello FT8 / FT4 — DT Correction

1. Leggere il valore **DT** da WSJT-X, JTDX o MSHV (es. `+0.8` o `-1.2`).
2. Inserirlo nel campo **DT value (s)** e premere **APPLY DT** — la correzione viene applicata con segno invertito.
3. Usare i **pulsanti quick** (±0.1s … ±2s) per correzioni istantanee.
4. La **barra di tolleranza**: verde |DT| < 0.5s ✓, arancione < 1s ⚠, rosso ≥ 1s ✗.

Riferimento visivo del pannello operativo:

![Pannello operativo SYSCLOCK](images/2.png)

#### Pannello SET EXACT TIME

1. Data nel formato `YYYY-MM-DD`, ora nel formato `HH:MM:SS`.
2. **NOW** precompila con l'ora corrente del sistema.
3. **SET** applica al sistema.

#### Pannello NTP

- Indicatore colorato: verde = NTP attivo, rosso = NTP inattivo.
- **ENABLE NTP** — unmask + riabilita sincronizzazione automatica.
- **DISABLE NTP** — disabilita completamente: ferma, disabilita e maschera tutti i demoni noti (incluso `systemd-timesyncd.socket`) + reset PLL kernel Linux.
- **RESTORE CLOCK FROM SNAPSHOT** — ripristina l'ora OS dal snapshot salvato al DISABLE NTP, usando il contatore monotono. Nessuna rete richiesta.

#### Pannello TIMEZONE

Selezionare il fuso orario e premere **APPLY**.

#### Grafico OFFSET HISTORY

Trend dell'offset cumulativo aggiornato ogni 500ms. Min/max sotto il grafico. Linea tratteggiata = zero.

---

### Note e avvertenze

- Su **Linux**: `clock_settime` via libc (nanosecondo) + `adjtimex` reset PLL dopo ogni correzione.
- Su **Linux**: **DISABLE NTP** maschera anche `systemd-timesyncd.socket` per impedire il riavvio automatico via socket activation.
- Su **macOS**: il reset del PLL del kernel non è applicabile. Alcuni comandi richiedono sudo senza password.
- Su **Windows**: `SetLocalTime()` via WinAPI (millisecondo). Richiede Prompt come Amministratore.
- L'**offset counter** è locale all'applicazione e si azzera alla chiusura.
- Le funzioni Linux (`clock_settime`, `adjtimex`) non vengono mai chiamate su macOS o Windows.

---

### Licenza

```
SYSCLOCK — System Time Control
Copyright (C) 2026  Alessandro Orlando

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```

---

## 🇬🇧 English

### Description

**SYSCLOCK — System Time Control** is a desktop GUI application written entirely in **Python 3** using the standard **tkinter** library, with no external dependencies.

Designed specifically for **amateur radio operators (ham radio)** working with **weak-signal digital modes** (FT8, FT4, JT65, JT9 and similar), where system clock accuracy is critical. It allows quick clock correction directly from the **DT** value reported by WSJT-X, JTDX or MSHV, and manages NTP, timezone and exact time in a single interface.

---

### Why Ham Radio Operators Need It

Weak-signal modes like **FT8** and **FT4** rely on fixed 15-second time slots synchronized to UTC. A clock drift of just 1–2 seconds causes decoding failures and makes transmission impossible. The **DT** (Delta Time) value shown by WSJT-X, JTDX and MSHV indicates exactly this offset.

SYSCLOCK allows you to:

- Correct the PC clock in one click by entering the DT value
- Operate **without internet** (portable ops, contests, SOTA, POTA)
- Fully disable NTP to prevent the sync daemon from reintroducing drift
- Set time manually from a GPS or atomic clock reference
- Visually monitor accumulated drift via the history chart

| Situation | How to use SYSCLOCK |
|---|---|
| DT in WSJT-X is ±0.5s or more | Enter DT value in the FT8 panel and press **APPLY DT** |
| Portable operation without internet | Disable NTP, set exact time from GPS with **SET EXACT TIME** |
| Progressive drift during a contest | Monitor history chart and apply DT corrections on the fly |
| NTP unavailable or unreliable | Disable NTP and use **RESTORE CLOCK FROM SNAPSHOT** |
| Timezone change while travelling | Update the OS with the **TIMEZONE** panel in one click |

> **Compatible with WSJT-X · JTDX · MSHV**

---

### Technical Description

| Item | Detail |
|---|---|
| Language | Python 3.8+ |
| GUI toolkit | tkinter (stdlib) + ttk |
| External dependencies | **None** |
| Operating systems | Linux, macOS, Windows |
| Required privileges | root / administrator for system operations |
| Architecture | Single-file, multi-thread with thread-safe queue (queue.Queue) |
| License | GNU GPL v3.0 |

#### Functions currently in use

| Function | Description |
|---|---|
| `_linux_set_clock(dt)` | Sets `CLOCK_REALTIME` via `clock_settime()` (libc, ns) + PLL reset via `adjtimex(2)` |
| `set_system_time(dt)` | Multi-OS wrapper: libc on Linux, `date` on macOS, `SetLocalTime` WinAPI on Windows |
| `ntp_enable()` | Unmasks and re-enables all known NTP daemons via `timedatectl` and `systemctl` |
| `ntp_disable()` | Stops, disables and **masks** all NTP daemons (including activation socket) + kernel PLL reset |
| `ntp_status()` | Checks if NTP is active (`timedatectl` + `systemctl is-active` for each known daemon) |
| `get_timezones()` | Retrieves available timezone list (timedatectl / zoneinfo / tzutil) |
| `set_timezone(tz)` | Sets system timezone (`timedatectl` / `systemsetup` / `tzutil`) |
| `RingBuffer` | Thread-safe circular buffer for offset history (120 samples, ~2 min) |
| `SysClockApp` | Main application class (tkinter.Tk), producer/consumer architecture |
| `_do_step(ms)` | Computes target from monotonic reference, sends syscall to worker thread |
| `_tick()` | Main loop (500ms): drains queue, updates display, offset, history, chart |
| `_restore_clock()` | Restores OS time from monotonic snapshot — no network, no subprocess |

#### System commands per OS

| OS | Operation | Method |
|---|---|---|
| Linux | Set time | `clock_settime(CLOCK_REALTIME)` via libc ctypes (nanosec) |
| Linux | Stop drift | `adjtimex(2)` PLL reset — complete Timex struct 208 bytes |
| Linux | NTP disable | `timedatectl set-ntp false` + `systemctl stop/disable/mask` + PLL reset |
| Linux | NTP enable | `systemctl unmask` + `timedatectl set-ntp true` |
| Linux | Timezone | `timedatectl set-timezone` |
| macOS | Set time | `date <MMDDHHmmYYYY.SS>` (sudo) |
| macOS | NTP | `systemsetup -setusingnetworktime on/off` |
| macOS | Timezone | `systemsetup -settimezone` |
| Windows | Set time | `SetLocalTime()` WinAPI via ctypes (millisec) |
| Windows | NTP | `net start/stop w32time`, `w32tm /resync`, `sc config` |
| Windows | Timezone | `tzutil /s` |

---

### Features

- **Live clock** — time and date updated every 500ms, computed from monotonic reference (immune to OS drift)
- **FT8/FT4 DT Correction** — enter DT from WSJT-X/JTDX/MSHV, correction applied with inverted sign; visual tolerance bar (green < 0.5s, orange < 1s, red ≥ 1s)
- **Quick DT buttons** — instant corrections of ±0.1s, ±0.5s, ±1s, ±2s
- **Set exact time** — manual `YYYY-MM-DD / HH:MM:SS` entry with **NOW** button
- **Full NTP management** — ENABLE / DISABLE with daemon masking; real-time status indicator
- **Restore clock from snapshot** — restores OS clock from monotonic snapshot saved at DISABLE NTP — no network required
- **Timezone management** — dropdown with all available timezones, applied immediately
- **Offset history chart** — sparkline of last 2 minutes, thread-safe
- **Operations log** — timestamped, color-coded by result
- **Linux, macOS and Windows compatible** — each OS uses its own native APIs

---

### Usage Instructions

#### Installation

##### 🐧 Linux

```bash
python3 -c "import tkinter; print('OK')"
sudo apt install python3-tk     # Debian/Ubuntu
sudo dnf install python3-tkinter # Fedora
sudo pacman -S tk                # Arch

sudo python3 sysclock_gui.py
```

##### 🍎 macOS

```bash
brew install python3
brew install python-tk   # if tkinter missing
sudo python3 sysclock_gui.py
```

##### 🪟 Windows

Install Python 3.8+ from [python.org](https://www.python.org/downloads/windows/) with **"Add Python to PATH"**. Launch from **Administrator Command Prompt**:

```cmd
cd C:\path\to\folder
python sysclock_gui.py
```

##### 🪟 Windows 11 — Standalone Executable

A pre-built version compatible with **Windows 11** is available, requiring no Python installation.
The executable is located in the `dist` folder:

```
dist\SysClockControl.exe
```

> **Important:** launch `SysClockControl.exe` by **right-clicking → Run as administrator**, as system-level operations require elevated privileges.

#### Quick Launch Reference

| System | Command |
|---|---|
| Linux | `sudo python3 sysclock_gui.py` |
| macOS | `sudo python3 sysclock_gui.py` |
| Windows | Administrator Command Prompt → `python sysclock_gui.py` |
| Windows 11 (standalone) | `dist\SysClockControl.exe` — right-click → **Run as administrator** |

---

#### FT8 / FT4 — DT Correction Panel

1. Read the **DT** value from WSJT-X, JTDX or MSHV (e.g. `+0.8` or `-1.2`).
2. Enter it in the **DT value (s)** field and press **APPLY DT** — correction is applied with inverted sign.
3. Use the **quick buttons** (±0.1s … ±2s) for instant corrections.
4. **Tolerance bar**: green |DT| < 0.5s ✓, orange < 1s ⚠, red ≥ 1s ✗.

Operational panel visual reference:

![SYSCLOCK operational panel](images/2.png)

#### SET EXACT TIME Panel

Date `YYYY-MM-DD`, time `HH:MM:SS`. **NOW** pre-fills current time. **SET** applies to system.

#### NTP Panel

- Green dot = NTP active, red = inactive.
- **ENABLE NTP** — unmask + re-enable automatic sync.
- **DISABLE NTP** — full disable: stops, disables and masks all known daemons (including `systemd-timesyncd.socket`) + Linux kernel PLL reset.
- **RESTORE CLOCK FROM SNAPSHOT** — restores OS clock from snapshot saved at DISABLE NTP, using monotonic counter. No network required.

#### TIMEZONE Panel

Select timezone from dropdown and press **APPLY**.

#### OFFSET HISTORY Chart

Cumulative offset trend updated every 500ms. Min/max shown below. Dashed line = zero.

---

### Notes and Warnings

- On **Linux**: `clock_settime` via libc (nanosecond) + `adjtimex` PLL reset after every correction.
- On **Linux**: **DISABLE NTP** masks `systemd-timesyncd.socket` to prevent automatic restart via socket activation.
- On **macOS**: kernel PLL reset is not applicable.
- On **Windows**: `SetLocalTime()` via WinAPI (millisecond). Must launch from Administrator Command Prompt.
- The **offset counter** is local to the application and resets on close.
- Linux-specific functions (`clock_settime`, `adjtimex`) are never called on macOS or Windows.

---

### License

```
SYSCLOCK — System Time Control
Copyright (C) 2026  Alessandro Orlando

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```
