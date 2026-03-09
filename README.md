# SYSCLOCK — System Clock Manager

> © 2026 Alessandro Orlando — GNU General Public License v3.0

---

## 🇮🇹 Italiano

### Descrizione

**SYSCLOCK** è un'applicazione desktop con interfaccia grafica (GUI) scritta interamente in **Python 3** usando la libreria standard **tkinter**. Permette di gestire l'orologio di sistema in modo semplice e visivo, senza dipendenze esterne.

L'applicazione è ispirata allo strumento a riga di comando `ctweaktime`, del quale riproduce le funzionalità principali aggiungendo un'interfaccia grafica moderna, un grafico storico degli offset, sincronizzazione NTP e gestione del fuso orario.

#### Utilizzo in ambito Radioamatoriale — Modi digitali FT8, FT4 e altri

SYSCLOCK è particolarmente utile per i **radioamatori** che operano in ambito **Radioamatoriale** con i modi digitali come **FT8**, **FT4**, **JT65**, **JT9** e simili con software come:

- 🔵 **WSJT-X** (sviluppato da K1JT)
- 🟢 **JTDX** (fork ottimizzato di WSJT-X)
- 🟡 **MSHV** (multi-mode, sviluppato da LZ2HV)

Questi modi digitali sono **estremamente sensibili alla sincronizzazione dell'orologio**: il protocollo FT8, ad esempio, utilizza slot temporali di esattamente 15 secondi e richiede che l'orologio del computer sia sincronizzato con il tempo UTC con una tolleranza di **±1 secondo** (idealmente entro ±0,5 s). Un orologio non sincronizzato causa mancate decodifiche e impossibilità di trasmettere correttamente.

**Casi d'uso tipici:**

| Situazione | Come usare SYSCLOCK |
|---|---|
| Orologio lento/veloce di qualche secondo | Usare i pulsanti **BACK / FORWARD** con passo 1s per correggere con precisione |
| Operazione portatile senza internet | Correggere manualmente l'ora con riferimento a un GPS o orologio atomico |
| Deriva dell'orologio durante un contest | Monitorare il grafico storico e correggere al volo senza uscire da WSJT-X |
| NTP non disponibile o non affidabile | Disabilitare NTP e gestire l'ora manualmente con step fini (10–100 ms) |
| Cambio di fuso orario in trasferta | Usare il pannello Timezone per aggiornare il SO in un click |

> 💡 **Consiglio pratico:** Prima di una sessione FT8, verificare la sincronizzazione con un server NTP affidabile (es. `pool.ntp.org`) tramite il pulsante **ENABLE NTP**. Se si opera in assenza di connessione internet, usare SYSCLOCK per allineare manualmente l'orologio a un riferimento GPS prima di avviare WSJT-X / JTDX / MSHV.

---

### Descrizione tecnica

| Voce | Dettaglio |
|---|---|
| Linguaggio | Python 3.8+ |
| GUI toolkit | tkinter (stdlib) + ttk |
| Dipendenze esterne | **Nessuna** |
| Sistemi operativi | Linux, macOS, Windows |
| Privilegi richiesti | root / amministratore per le operazioni di sistema |
| Architettura | Single-file, multi-thread (operazioni di sistema in thread separati) |
| Licenza | GNU GPL v3.0 |

#### Componenti interni

| Modulo / Classe | Funzione |
|---|---|
| `set_system_time(dt)` | Imposta l'orologio di sistema a un datetime preciso |
| `step_system_time(ms)` | Avanza o ritarda l'orologio di un numero di millisecondi |
| `get_timezones()` | Recupera l'elenco dei fusi orari disponibili |
| `set_timezone(tz)` | Imposta il fuso orario di sistema |
| `ntp_sync(enable)` | Abilita o disabilita la sincronizzazione NTP |
| `get_ntp_status()` | Legge lo stato corrente di NTP |
| `RingBuffer` | Buffer circolare per lo storico degli offset (120 campioni) |
| `SysClockApp` | Classe principale dell'applicazione (tkinter.Tk) |

#### Comandi di sistema utilizzati

| OS | Comando |
|---|---|
| Linux | `date -s`, `timedatectl set-time`, `timedatectl set-ntp`, `timedatectl set-timezone`, `timedatectl list-timezones` |
| macOS | `date <timestamp>`, `systemsetup -settimezone`, `systemsetup -setusingnetworktime` |
| Windows | `SetLocalTime` (ctypes/WinAPI), `tzutil /s`, `tzutil /l`, `w32tm /resync`, `net start/stop w32time`, `sc query w32time` |

---

### Funzionalità

- **Orologio live** — visualizza ora e data aggiornate ogni secondo
- **Step avanti/indietro** — sposta l'orologio di un passo configurabile (da 10 ms a 60 s)
- **Preset rapidi** — pulsanti preimpostati: 10ms, 50ms, 100ms, 500ms, 1s, 5s, 30s, 60s
- **Slider personalizzato** — scelta libera del passo tra 10 ms e 60.000 ms
- **Imposta ora esatta** — inserimento manuale di data e ora nel formato `YYYY-MM-DD / HH:MM:SS`
- **Sincronizzazione NTP** — abilita/disabilita NTP con un click, con indicatore di stato
- **Gestione fuso orario** — menu a tendina con tutti i timezone disponibili, applicazione immediata
- **Grafico storico** — sparkline degli ultimi 2 minuti di offset accumulato
- **Log operazioni** — registro timestampato di tutte le azioni, con colori per esito (verde/rosso/blu)
- **Reset offset** — azzera il contatore cumulativo
- **Scorciatoie da tastiera** — controllo completo da tastiera senza mouse

---

### Istruzioni d'uso

#### Installazione per sistema operativo

---

##### 🐧 Linux

1. **Verifica Python e tkinter**

```bash
python3 --version
python3 -c "import tkinter; print('tkinter OK')"
```

2. **Se tkinter non è installato**, installarlo con il gestore pacchetti:

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install python3-tk

# Fedora / RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

3. **Avvio** (richiede root per modificare l'orologio):

```bash
sudo python3 sysclock_gui.py
```

> 💡 Se `sudo` richiede la password ad ogni avvio, aggiungere la riga seguente a `/etc/sudoers` (con `visudo`) per consentire i comandi necessari senza password:
> ```
> tuo_utente ALL=(ALL) NOPASSWD: /usr/bin/timedatectl, /usr/bin/date
> ```

---

##### 🍎 macOS

1. **Verifica Python** — macOS include Python 3 dalla versione 12.3+. In alternativa installare tramite [Homebrew](https://brew.sh):

```bash
brew install python3
```

2. **Verifica tkinter**:

```bash
python3 -c "import tkinter; print('tkinter OK')"
```

3. Se tkinter non è disponibile:

```bash
brew install python-tk
```

4. **Avvio** (richiede privilegi amministratore):

```bash
sudo python3 sysclock_gui.py
```

> ⚠️ Su macOS Monterey e versioni successive, potrebbe essere necessario concedere i permessi di accesso al sistema nelle **Preferenze di Sistema → Privacy e sicurezza**.

---

##### 🪟 Windows

1. **Scarica Python** da [python.org](https://www.python.org/downloads/windows/) e installa la versione 3.8 o superiore. Durante l'installazione selezionare **"Add Python to PATH"**.

2. **Verifica l'installazione** (tkinter è incluso di default nell'installer ufficiale):

```cmd
python --version
python -c "import tkinter; print('tkinter OK')"
```

3. **Avvio come Amministratore** — obbligatorio per modificare l'orologio di sistema:

   - Cercare **Prompt dei comandi** nel menu Start
   - Fare clic destro → **Esegui come amministratore**
   - Nella finestra che si apre, navigare nella cartella del file:

```cmd
cd C:\percorso\della\cartella
python sysclock_gui.py
```

   In alternativa, creare un collegamento sul Desktop con:
   - Destinazione: `python.exe C:\percorso\sysclock_gui.py`
   - Avanzate → **Esegui come amministratore** ✓

> ⚠️ Senza privilegi di Amministratore le funzioni di modifica dell'ora, NTP e timezone non avranno effetto. L'applicazione lo segnala con l'indicatore **NO ROOT** nella barra del titolo.

---

#### Avvio — riepilogo rapido

| Sistema | Comando |
|---|---|
| Linux | `sudo python3 sysclock_gui.py` |
| macOS | `sudo python3 sysclock_gui.py` |
| Windows | Prompt dei comandi come Amministratore → `python sysclock_gui.py` |

#### Scorciatoie da tastiera

| Tasto | Azione |
|---|---|
| `<` oppure `,` | Sposta l'orologio **indietro** del passo corrente |
| `>` oppure `.` | Sposta l'orologio **avanti** del passo corrente |
| `+` oppure `=` | **Aumenta** il passo al preset successivo |
| `-` oppure `_` | **Diminuisce** il passo al preset precedente |
| `Q` oppure `Esc` | **Chiude** l'applicazione |

#### Pannello Step Controls

1. Scegliere un passo dai **pulsanti preset** oppure usare lo **slider** per un valore personalizzato.
2. Cliccare **◀◀ BACK** per spostare l'orologio indietro, **FORWARD ▶▶** per spostarlo avanti.
3. Il totale dell'offset accumulato è sempre visibile nel pannello in alto a sinistra.
4. Cliccare **RESET OFFSET** per azzerare il contatore (non modifica l'orologio di sistema).

#### Pannello Set Exact Time

1. Inserire la data nel campo **Date** nel formato `YYYY-MM-DD`.
2. Inserire l'ora nel campo **Time** nel formato `HH:MM:SS`.
3. Cliccare **NOW** per pre-compilare automaticamente l'ora corrente.
4. Cliccare **SET** per applicare la data/ora al sistema.

#### Pannello NTP

- Lo stato NTP (attivo / inattivo) è indicato da un pallino colorato (verde = attivo).
- Cliccare **ENABLE NTP** per abilitare la sincronizzazione automatica dell'ora.
- Cliccare **DISABLE NTP** per disabilitarla (necessario prima di modificare l'ora manualmente su Linux).

#### Pannello Timezone

1. Selezionare il fuso orario desiderato dal menu a tendina.
2. Cliccare **APPLY** per impostarlo nel sistema.

#### Grafico storico

Il grafico mostra l'andamento dell'offset cumulativo aggiornato ogni secondo. I valori minimi e massimi sono riportati sotto il grafico. La linea tratteggiata orizzontale rappresenta lo zero.

---

### Note e avvertenze

- Su **Linux**, se `sudo` è configurato senza password (`NOPASSWD`), i comandi vengono eseguiti silenziosamente. Altrimenti potrebbe essere necessario inserire la password nel terminale da cui si avvia l'applicazione.
- Su **macOS**, alcuni comandi richiedono che `sudo` non richieda password per l'utente corrente oppure che si usi `su`.
- Su **Windows**, l'applicazione usa direttamente le API di sistema (`SetLocalTime` via ctypes, `tzutil`, `w32tm`) senza passare per `cmd`. È necessario avviare il programma da un **Prompt dei comandi con privilegi di Amministratore**.
- La modifica dell'ora di sistema con **NTP attivo** su Linux verrà sovrascritta automaticamente dal demone NTP. Disabilitare NTP prima di effettuare modifiche manuali. Su Windows, il servizio `w32time` viene gestito tramite i pulsanti NTP dell'applicazione.
- Il **contatore offset** è puramente informativo e locale all'applicazione: viene azzerato alla chiusura del programma.

---
---

## 🇬🇧 English

### Description

**SYSCLOCK** is a desktop application with a graphical user interface (GUI) written entirely in **Python 3** using the built-in **tkinter** library. It allows easy, visual management of the system clock with no external dependencies.

The application is inspired by the `ctweaktime` command-line tool, reproducing its core features while adding a modern GUI, an offset history chart, NTP synchronization, and timezone management.

#### Amateur Radio Use — FT8, FT4 and Other Digital Modes

SYSCLOCK is especially useful for **amateur radio operators** working in the **Amateur Radio** field with digital modes such as **FT8**, **FT4**, **JT65**, **JT9** and similar, using software like:

- 🔵 **WSJT-X** (developed by K1JT)
- 🟢 **JTDX** (optimised WSJT-X fork)
- 🟡 **MSHV** (multi-mode software by LZ2HV)

These digital modes are **extremely sensitive to clock synchronisation**: the FT8 protocol, for example, uses fixed 15-second time slots and requires the computer clock to be synchronised to UTC within **±1 second** (ideally within ±0.5 s). An unsynchronised clock causes missed decodes and prevents correct transmission.

**Typical use cases:**

| Situation | How to use SYSCLOCK |
|---|---|
| Clock running a few seconds fast or slow | Use **BACK / FORWARD** buttons with a 1s step to correct precisely |
| Portable operation without internet | Manually set the time using a GPS or atomic clock reference |
| Clock drift during a contest | Monitor the history chart and correct on the fly without leaving WSJT-X |
| NTP unavailable or unreliable | Disable NTP and manage time manually with fine steps (10–100 ms) |
| Timezone change when operating away from home | Use the Timezone panel to update the OS in one click |

> 💡 **Practical tip:** Before an FT8 session, verify synchronisation with a reliable NTP server (e.g. `pool.ntp.org`) using the **ENABLE NTP** button. If operating without an internet connection, use SYSCLOCK to manually align the clock to a GPS reference before launching WSJT-X / JTDX / MSHV.

---

### Technical Description

| Item | Detail |
|---|---|
| Language | Python 3.8+ |
| GUI toolkit | tkinter (stdlib) + ttk |
| External dependencies | **None** |
| Operating systems | Linux, macOS, Windows |
| Required privileges | root / administrator for system operations |
| Architecture | Single-file, multi-threaded (system calls run in background threads) |
| License | GNU GPL v3.0 |

#### Internal Components

| Module / Class | Purpose |
|---|---|
| `set_system_time(dt)` | Sets the system clock to a precise datetime |
| `step_system_time(ms)` | Advances or rewinds the clock by a number of milliseconds |
| `get_timezones()` | Retrieves the list of available timezones |
| `set_timezone(tz)` | Sets the system timezone |
| `ntp_sync(enable)` | Enables or disables NTP synchronization |
| `get_ntp_status()` | Reads the current NTP status |
| `RingBuffer` | Circular buffer for offset history (120 samples) |
| `SysClockApp` | Main application class (tkinter.Tk) |

#### System Commands Used

| OS | Command |
|---|---|
| Linux | `date -s`, `timedatectl set-time`, `timedatectl set-ntp`, `timedatectl set-timezone`, `timedatectl list-timezones` |
| macOS | `date <timestamp>`, `systemsetup -settimezone`, `systemsetup -setusingnetworktime` |
| Windows | `SetLocalTime` (ctypes/WinAPI), `tzutil /s`, `tzutil /l`, `w32tm /resync`, `net start/stop w32time`, `sc query w32time` |

---

### Features

- **Live clock** — displays current time and date, updated every second
- **Step forward/backward** — shifts the clock by a configurable step (from 10 ms to 60 s)
- **Quick presets** — preset buttons: 10ms, 50ms, 100ms, 500ms, 1s, 5s, 30s, 60s
- **Custom slider** — freely choose the step between 10 ms and 60,000 ms
- **Set exact time** — manually enter a date and time in `YYYY-MM-DD / HH:MM:SS` format
- **NTP synchronization** — enable/disable NTP with one click, with status indicator
- **Timezone management** — dropdown menu with all available timezones, applied immediately
- **History chart** — sparkline of the last 2 minutes of accumulated offset
- **Operations log** — timestamped log of all actions, color-coded by result (green/red/blue)
- **Reset offset** — clears the cumulative counter
- **Keyboard shortcuts** — full keyboard control without a mouse

---

### Usage Instructions

#### Installation by Operating System

---

##### 🐧 Linux

1. **Check Python and tkinter**

```bash
python3 --version
python3 -c "import tkinter; print('tkinter OK')"
```

2. **If tkinter is not installed**, install it with your package manager:

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install python3-tk

# Fedora / RHEL
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

3. **Launch** (root required to modify the clock):

```bash
sudo python3 sysclock_gui.py
```

> 💡 If `sudo` asks for a password every time, add the following line to `/etc/sudoers` (using `visudo`) to allow the required commands without a password:
> ```
> your_user ALL=(ALL) NOPASSWD: /usr/bin/timedatectl, /usr/bin/date
> ```

---

##### 🍎 macOS

1. **Check Python** — macOS includes Python 3 from version 12.3+. Alternatively, install via [Homebrew](https://brew.sh):

```bash
brew install python3
```

2. **Check tkinter**:

```bash
python3 -c "import tkinter; print('tkinter OK')"
```

3. If tkinter is not available:

```bash
brew install python-tk
```

4. **Launch** (administrator privileges required):

```bash
sudo python3 sysclock_gui.py
```

> ⚠️ On macOS Monterey and later, you may need to grant system access permissions in **System Preferences → Privacy & Security**.

---

##### 🪟 Windows

1. **Download Python** from [python.org](https://www.python.org/downloads/windows/) and install version 3.8 or later. During installation, check **"Add Python to PATH"**.

2. **Verify the installation** (tkinter is included by default in the official installer):

```cmd
python --version
python -c "import tkinter; print('tkinter OK')"
```

3. **Launch as Administrator** — required to modify the system clock:

   - Search for **Command Prompt** in the Start menu
   - Right-click → **Run as administrator**
   - In the window that opens, navigate to the folder containing the file:

```cmd
cd C:\path\to\folder
python sysclock_gui.py
```

   Alternatively, create a Desktop shortcut with:
   - Target: `python.exe C:\path\to\sysclock_gui.py`
   - Advanced → **Run as administrator** ✓

> ⚠️ Without Administrator privileges, the time, NTP and timezone functions will have no effect. The application signals this with the **NO ROOT** indicator in the title bar.

---

#### Launch — quick reference

| System | Command |
|---|---|
| Linux | `sudo python3 sysclock_gui.py` |
| macOS | `sudo python3 sysclock_gui.py` |
| Windows | Command Prompt as Administrator → `python sysclock_gui.py` |

#### Keyboard Shortcuts

| Key | Action |
|---|---|
| `<` or `,` | Move the clock **backward** by the current step |
| `>` or `.` | Move the clock **forward** by the current step |
| `+` or `=` | **Increase** the step to the next preset |
| `-` or `_` | **Decrease** the step to the previous preset |
| `Q` or `Esc` | **Quit** the application |

#### Step Controls Panel

1. Choose a step using the **preset buttons** or the **slider** for a custom value.
2. Click **◀◀ BACK** to move the clock backward, **FORWARD ▶▶** to move it forward.
3. The total accumulated offset is always shown in the top-left panel.
4. Click **RESET OFFSET** to zero the counter (does not modify the system clock).

#### Set Exact Time Panel

1. Enter the date in the **Date** field in `YYYY-MM-DD` format.
2. Enter the time in the **Time** field in `HH:MM:SS` format.
3. Click **NOW** to automatically fill in the current time.
4. Click **SET** to apply the date/time to the system.

#### NTP Panel

- The NTP status (active / inactive) is shown by a colored dot (green = active).
- Click **ENABLE NTP** to enable automatic time synchronization.
- Click **DISABLE NTP** to disable it (required before manually changing the time on Linux).

#### Timezone Panel

1. Select the desired timezone from the dropdown menu.
2. Click **APPLY** to set it on the system.

#### History Chart

The chart shows the cumulative offset trend, updated every second. Minimum and maximum values are displayed below the chart. The dashed horizontal line represents zero.

---

### Notes and Warnings

- On **Linux**, if `sudo` is configured without a password (`NOPASSWD`), commands run silently. Otherwise you may need to enter your password in the terminal from which the application is launched.
- On **macOS**, some commands require that `sudo` does not prompt for a password for the current user, or that `su` is used instead.
- On **Windows**, the application uses system APIs directly (`SetLocalTime` via ctypes, `tzutil`, `w32tm`) without going through `cmd`. The program must be launched from a **Command Prompt with Administrator privileges**.
- Manually changing the system time with **NTP active** on Linux will be overwritten automatically by the NTP daemon. Disable NTP before making manual changes. On Windows, the `w32time` service is managed through the NTP buttons in the application.
- The **offset counter** is purely informational and local to the application: it resets when the program is closed.

---

### License

```
SYSCLOCK — System Clock Manager
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
