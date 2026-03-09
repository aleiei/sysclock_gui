#!/usr/bin/env python3
"""
sysclock_gui.py  —  System Time Control
Modifica l'orario di sistema, sincronizza NTP, gestisce timezone.
Richiede privilegi root/admin per le operazioni di sistema.

Copyright (C) 2026  Alessandro Orlando
License: GNU General Public License v3.0 (GPL-3.0)
         https://www.gnu.org/licenses/gpl-3.0.html
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import queue
import datetime
import time
import platform
import os
import sys
import collections
import ctypes
import ctypes.util

# ─────────────────────────────────────────────────────────────── Palette ──
C = {
    "bg":      "#0b0e13",
    "panel":   "#10141c",
    "panel2":  "#161c28",
    "border":  "#1e2a3a",
    "accent":  "#38bdf8",
    "accent2": "#f472b6",
    "accent3": "#34d399",
    "warn":    "#fb923c",
    "err":     "#f87171",
    "txt":     "#e2e8f0",
    "txt_dim": "#7a9aba",
    "txt_med": "#a8c0d6",
}

OS = platform.system()   # "Linux" | "Darwin" | "Windows"

# ══════════════════════════════════════ ctypes setup (Linux, built once) ══

if OS == "Linux":
    _libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6",
                        use_errno=True)

    class _Timespec(ctypes.Structure):
        _fields_ = [("tv_sec",  ctypes.c_long),
                    ("tv_nsec", ctypes.c_long)]

    _libc.clock_settime.argtypes = [ctypes.c_int, ctypes.c_void_p]
    _libc.clock_settime.restype  = ctypes.c_int

    class _Timex(ctypes.Structure):
        """Complete struct timex for 64-bit Linux = 208 bytes."""
        _fields_ = [
            ("modes",    ctypes.c_uint),  ("offset",   ctypes.c_long),
            ("freq",     ctypes.c_long),  ("maxerror", ctypes.c_long),
            ("esterror", ctypes.c_long),  ("status",   ctypes.c_int),
            ("constant", ctypes.c_long),  ("precision",ctypes.c_long),
            ("tolerance",ctypes.c_long),  ("time_sec", ctypes.c_long),
            ("time_usec",ctypes.c_long),  ("tick",     ctypes.c_long),
            ("ppsfreq",  ctypes.c_long),  ("jitter",   ctypes.c_long),
            ("shift",    ctypes.c_int),   ("stabil",   ctypes.c_long),
            ("jitcnt",   ctypes.c_long),  ("calcnt",   ctypes.c_long),
            ("errcnt",   ctypes.c_long),  ("stbcnt",   ctypes.c_long),
            ("tai",      ctypes.c_int),
            ("_p0",ctypes.c_int),("_p1",ctypes.c_int),("_p2",ctypes.c_int),
            ("_p3",ctypes.c_int),("_p4",ctypes.c_int),("_p5",ctypes.c_int),
            ("_p6",ctypes.c_int),("_p7",ctypes.c_int),("_p8",ctypes.c_int),
            ("_p9",ctypes.c_int),("_p10",ctypes.c_int),
        ]

    _ADJ_OFFSET    = 0x0001
    _ADJ_FREQUENCY = 0x0002
    _ADJ_STATUS    = 0x0010
    _STA_UNSYNC    = 0x0040
    _CLOCK_REALTIME = 0

# ══════════════════════════════════════════════════════ System functions ══

def _is_admin() -> bool:
    if OS == "Windows":
        try: return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except: return False
    return os.geteuid() == 0


def _run(cmd, use_sudo=False):
    if use_sudo and OS != "Windows" and not _is_admin():
        cmd = ["sudo", "-n"] + list(cmd)
    try:
        r = subprocess.run(list(cmd), capture_output=True, text=True, timeout=10)
        return r.returncode == 0, r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError as e: return False, "", str(e)
    except subprocess.TimeoutExpired: return False, "", "timeout"


def _linux_set_clock(dt: datetime.datetime) -> tuple:
    """clock_settime + adjtimex reset. Pure ctypes — never blocks tkinter.
    dt is naive local time. dt.timestamp() converts local→UTC epoch correctly."""
    epoch_i = int(dt.timestamp())          # integer seconds since epoch (UTC)
    nsec    = dt.microsecond * 1000        # nanoseconds from microseconds only
    ts = _Timespec(epoch_i, nsec)
    if _libc.clock_settime(_CLOCK_REALTIME, ctypes.byref(ts)) != 0:
        return False, f"clock_settime errno={ctypes.get_errno()}"
    tx = _Timex()
    tx.modes  = _ADJ_OFFSET | _ADJ_FREQUENCY | _ADJ_STATUS
    tx.offset = 0; tx.freq = 0; tx.status = _STA_UNSYNC
    _libc.adjtimex(ctypes.byref(tx))
    return True, "OK"


def set_system_time(dt: datetime.datetime) -> tuple:
    if OS == "Linux":
        return _linux_set_clock(dt)
    elif OS == "Darwin":
        ok, _, e = _run(["date", dt.strftime("%m%d%H%M%Y.%S")], use_sudo=True)
        return ok, "OK" if ok else e
    elif OS == "Windows":
        class ST(ctypes.Structure):
            _fields_ = [("wYear",ctypes.c_uint16),("wMonth",ctypes.c_uint16),
                        ("wDayOfWeek",ctypes.c_uint16),("wDay",ctypes.c_uint16),
                        ("wHour",ctypes.c_uint16),("wMinute",ctypes.c_uint16),
                        ("wSecond",ctypes.c_uint16),("wMilliseconds",ctypes.c_uint16)]
        st = ST(dt.year,dt.month,0,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond//1000)
        ok = bool(ctypes.windll.kernel32.SetLocalTime(ctypes.byref(st)))
        return ok, "OK" if ok else "SetLocalTime failed"
    return False, "Unsupported OS"


# All NTP-related units we stop/mask on disable — must be unmasked on enable
_NTP_UNITS = (
    "systemd-timesyncd",
    "systemd-timesyncd.socket",
    "chronyd",
    "ntp",
    "ntpd",
    "openntpd",
    "ntpsec",
)

def ntp_enable() -> tuple:
    if OS == "Linux":
        # Unmask every unit we may have masked (same list used by disable)
        for s in _NTP_UNITS:
            _run(["systemctl","unmask",s], use_sudo=True)
        # timedatectl picks the right backend automatically
        _run(["timedatectl","set-ntp","true"], use_sudo=True)
        return True, "NTP enabled"
    elif OS == "Darwin":
        ok,_,e = _run(["systemsetup","-setusingnetworktime","on"], use_sudo=True)
        return ok, "OK" if ok else e
    elif OS == "Windows":
        _run(["sc","config","w32time","start=auto"])
        _run(["net","start","w32time"])
        ok,_,e = _run(["w32tm","/resync","/force"])
        return ok, "OK" if ok else e
    return False, "Unsupported OS"


def ntp_disable() -> tuple:
    if OS == "Linux":
        _run(["timedatectl","set-ntp","false"], use_sudo=True)
        # Stop and mask every unit (including the socket that can auto-restart
        # the daemon even after stop+disable)
        for s in _NTP_UNITS:
            _run(["systemctl","stop",   s], use_sudo=True)
            _run(["systemctl","disable",s], use_sudo=True)
            _run(["systemctl","mask",   s], use_sudo=True)
        # Reset kernel PLL — clears freq accumulator so kernel cannot drift clock
        tx = _Timex()
        tx.modes  = _ADJ_OFFSET | _ADJ_FREQUENCY | _ADJ_STATUS
        tx.offset = 0; tx.freq = 0; tx.status = _STA_UNSYNC
        _libc.adjtimex(ctypes.byref(tx))
        return True, "NTP disabled and masked"
    elif OS == "Darwin":
        ok,_,e = _run(["systemsetup","-setusingnetworktime","off"], use_sudo=True)
        return ok, "OK" if ok else e
    elif OS == "Windows":
        ok,_,e = _run(["net","stop","w32time"])
        return ok, "OK" if ok else e
    return False, "Unsupported OS"


def ntp_status() -> bool:
    if OS == "Linux":
        _,out,_ = _run(["timedatectl","show","--property=NTP","--value"])
        if out.strip().lower() == "yes": return True
        for s in ("systemd-timesyncd","chronyd","ntpd","ntpsec"):
            _,out2,_ = _run(["systemctl","is-active",s])
            if out2.strip() == "active": return True
        return False
    elif OS == "Darwin":
        _,out,_ = _run(["systemsetup","-getnetworktimeserver"])
        return "network time" in out.lower()
    elif OS == "Windows":
        _,out,_ = _run(["sc","query","w32time"])
        return "RUNNING" in out
    return False


def get_timezones() -> list:
    if OS == "Windows":
        ok,out,_ = _run(["tzutil","/l"])
        if ok:
            lines=[l.strip() for l in out.splitlines() if l.strip()]
            return sorted(lines[i] for i in range(1,len(lines),2))
    if OS == "Linux":
        ok,out,_ = _run(["timedatectl","list-timezones"])
        if ok: return out.splitlines()
    try:
        import zoneinfo; return sorted(zoneinfo.available_timezones())
    except ImportError: pass
    return ["UTC","Europe/Rome","America/New_York","Europe/London","Asia/Tokyo"]


def set_timezone(tz: str) -> tuple:
    if OS == "Windows":   ok,_,e = _run(["tzutil","/s",tz])
    elif OS == "Linux":   ok,_,e = _run(["timedatectl","set-timezone",tz], use_sudo=True)
    elif OS == "Darwin":  ok,_,e = _run(["systemsetup","-settimezone",tz], use_sudo=True)
    else: return False, "Unsupported OS"
    return ok, "OK" if ok else e

# ══════════════════════════════════════════════════════════ Ring buffer ══

class RingBuffer:
    def __init__(self, size):
        self._buf  = collections.deque(maxlen=size)
        self._lock = threading.Lock()
    def push(self, v):
        with self._lock: self._buf.append(v)
    def values(self):
        with self._lock: return list(self._buf)

# ════════════════════════════════════════════════════════ Widget helpers ══

def _lbl(parent, text="", fg=None, font=None, bg=None, **kw):
    return tk.Label(parent, text=text, fg=fg or C["txt"], bg=bg or C["bg"],
                    font=font or ("Courier New",10), **kw)

def _frm(parent, bg=None, **kw):
    return tk.Frame(parent, bg=bg or C["bg"], **kw)

def _panel(parent):
    return tk.Frame(parent, bg=C["panel"],
                    highlightbackground=C["border"], highlightthickness=1)

def _btn(parent, text, cmd, color=None, **kw):
    color = color or C["accent"]
    b = tk.Button(parent, text=text, command=cmd,
                  bg=C["panel2"], fg=color,
                  activebackground=color, activeforeground=C["bg"],
                  relief="flat", bd=0, cursor="hand2",
                  font=("Courier New",10,"bold"), padx=12, pady=6, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=color, fg=C["bg"]))
    b.bind("<Leave>", lambda e: b.config(bg=C["panel2"], fg=color))
    return b

def _div(parent):
    tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=6)

# ══════════════════════════════════════════════════════════ Application ══

class SysClockApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("SYSCLOCK — System Time Control")
        self.configure(bg=C["bg"])
        self.resizable(True, True)
        self.minsize(880, 620)

        self._running  = True
        self._total_ms = 0          # written only from main thread (_tick)
        self._history  = RingBuffer(120)
        self._tz_var   = tk.StringVar()

        # ── Monotonic reference ───────────────────────────────────────────
        # The GUI clock and step targets are ALWAYS computed from:
        #   now = wall_ref + (monotonic() - mono_ref)
        # This makes the display immune to OS clock drift and ensures steps
        # are applied relative to the true elapsed time, not datetime.now().
        self._mono_ref = time.monotonic()
        self._wall_ref = datetime.datetime.now()   # accurate at startup (NTP on)

        # Queue: worker threads → main thread (ms, ok, msg)
        self._step_q: queue.Queue = queue.Queue()

        self._build_ui()

        self.after(0, self._refresh_ntp_status_label)

        # Intercept window-close (X button) so destroy() always runs
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._tick()

    # ══════════════════════════════════════════════════════════ Build UI ══

    def _build_ui(self):
        # top bar
        top = _frm(self, bg=C["panel"])
        top.pack(fill="x")
        tk.Frame(top, bg=C["accent"], width=4).pack(side="left", fill="y")
        tb = _frm(top, bg=C["panel"]); tb.pack(side="left", padx=14, pady=12)
        _lbl(tb, "System Time Control", fg=C["accent"],
             font=("Courier New",18,"bold"), bg=C["panel"]).pack(anchor="w")
        _lbl(tb, "System Time Control  ·  © 2026 Alessandro Orlando  ·  GPL v3",
             fg=C["txt_dim"], font=("Courier New",7), bg=C["panel"]).pack(anchor="w")
        root_ok = _is_admin()
        _lbl(top, "ADMIN" if (root_ok and OS=="Windows") else ("ROOT" if root_ok else "NO ROOT"),
             fg=C["accent3"] if root_ok else C["warn"],
             font=("Courier New",9,"bold"), bg=C["panel"], padx=8).pack(side="right", pady=14)
        _lbl(top, f"● {OS}", fg=C["accent3"],
             font=("Courier New",9,"bold"), bg=C["panel"], padx=14).pack(side="right", pady=14)

        body = _frm(self); body.pack(fill="both", expand=True, padx=14, pady=12)
        left  = _frm(body); left.pack(side="left",  fill="both", expand=True, padx=(0,7))
        right = _frm(body); right.pack(side="left", fill="both", expand=True, padx=(7,0))

        self._build_clock_panel(left)
        self._build_dt_panel(left)
        self._build_manual_panel(left)
        self._build_ntp_panel(right)
        self._build_tz_panel(right)
        self._build_chart_panel(right)
        self._build_log_panel(right)

    # ── Clock panel ───────────────────────────────────────────────────────

    def _build_clock_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        _lbl(i,"SYSTEM TIME", fg=C["txt_dim"], font=("Courier New",8,"bold"),
             bg=C["panel"], anchor="w").pack(fill="x")
        self._clock_var = tk.StringVar(value="──:──:──")
        tk.Label(i, textvariable=self._clock_var, fg=C["accent"], bg=C["panel"],
                 font=("Courier New",42,"bold"), anchor="w").pack(fill="x")
        self._date_var = tk.StringVar(value="────────────")
        tk.Label(i, textvariable=self._date_var, fg=C["txt_med"], bg=C["panel"],
                 font=("Courier New",12), anchor="w").pack(fill="x")
        _div(i)
        row = _frm(i, bg=C["panel"]); row.pack(fill="x")
        self._offset_var = tk.StringVar(value="offset  +0 ms")
        _lbl(row, textvariable=self._offset_var, fg=C["txt_dim"],
             font=("Courier New",10), bg=C["panel"], anchor="w").pack(side="left")
        self._tz_display = tk.StringVar()
        _lbl(row, textvariable=self._tz_display, fg=C["txt_dim"],
             font=("Courier New",9), bg=C["panel"], anchor="e").pack(side="right")

    # ── FT8 DT panel ──────────────────────────────────────────────────────

    def _build_dt_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        hdr = _frm(i, bg=C["panel"]); hdr.pack(fill="x", pady=(0,6))
        _lbl(hdr,"FT8 / FT4  —  DT CORRECTION", fg=C["warn"],
             font=("Courier New",8,"bold"), bg=C["panel"], anchor="w").pack(side="left")
        _lbl(hdr,"WSJT-X · JTDX · MSHV", fg=C["txt_dim"],
             font=("Courier New",7), bg=C["panel"], anchor="e").pack(side="right")
        r1 = _frm(i, bg=C["panel"]); r1.pack(fill="x", pady=(0,6))
        _lbl(r1,"DT value (s):", fg=C["txt_med"],
             font=("Courier New",9), bg=C["panel"]).pack(side="left")
        self._dt_entry = tk.Entry(r1, bg=C["panel2"], fg=C["warn"],
                                  insertbackground=C["warn"], relief="flat", bd=0,
                                  font=("Courier New",13,"bold"), width=8, justify="center",
                                  highlightbackground=C["warn"], highlightthickness=1)
        self._dt_entry.insert(0,"0.0")
        self._dt_entry.pack(side="left", padx=(8,8))
        _btn(r1,"APPLY DT",  self._apply_dt,  color=C["warn"]).pack(side="left")
        _btn(r1,"CLEAR",
             lambda: (self._dt_entry.delete(0,"end"), self._dt_entry.insert(0,"0.0")),
             color=C["txt_dim"]).pack(side="left", padx=(6,0))
        r2 = _frm(i, bg=C["panel"]); r2.pack(fill="x", pady=(0,4))
        _lbl(r2,"quick:", fg=C["txt_dim"], font=("Courier New",9),
             bg=C["panel"]).pack(side="left", padx=(0,6))
        for ms in [-2000,-1000,-500,-100,100,500,1000,2000]:
            lbl = f"{ms//1000:+d}s" if abs(ms)>=1000 else f"{ms:+d}ms"
            col = C["accent2"] if ms<0 else C["accent"]
            b = _btn(r2, lbl, lambda v=ms: self._do_step(v), color=col)
            b.config(padx=6, pady=3)
            b.pack(side="left", padx=2)
        tr = _frm(i, bg=C["panel"]); tr.pack(fill="x", pady=(4,0))
        _lbl(tr,"tolerance:", fg=C["txt_dim"],
             font=("Courier New",8), bg=C["panel"]).pack(side="left", padx=(0,6))
        self._tol_canvas = tk.Canvas(tr, height=14, bg=C["panel2"], highlightthickness=0)
        self._tol_canvas.pack(side="left", fill="x", expand=True)
        self._tol_lbl = _lbl(tr,"DT = +0.000 s  ✓ OK",
                              fg=C["accent3"], font=("Courier New",8), bg=C["panel"])
        self._tol_lbl.pack(side="left", padx=(8,0))

    # ── Step controls ─────────────────────────────────────────────────────

    # ── Manual set time ───────────────────────────────────────────────────

    def _build_manual_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        _lbl(i,"SET EXACT TIME", fg=C["txt_dim"], font=("Courier New",8,"bold"),
             bg=C["panel"], anchor="w").pack(fill="x", pady=(0,8))
        row = _frm(i, bg=C["panel"]); row.pack(fill="x")
        _lbl(row,"Date:", fg=C["txt_dim"], font=("Courier New",9), bg=C["panel"]).pack(side="left")
        self._date_entry = tk.Entry(row, bg=C["panel2"], fg=C["txt"],
                                    insertbackground=C["accent"], relief="flat", bd=0,
                                    font=("Courier New",11), width=12,
                                    highlightbackground=C["border"], highlightthickness=1)
        self._date_entry.pack(side="left", padx=(6,12))
        _lbl(row,"Time:", fg=C["txt_dim"], font=("Courier New",9), bg=C["panel"]).pack(side="left")
        self._time_entry = tk.Entry(row, bg=C["panel2"], fg=C["txt"],
                                    insertbackground=C["accent"], relief="flat", bd=0,
                                    font=("Courier New",11), width=10,
                                    highlightbackground=C["border"], highlightthickness=1)
        self._time_entry.pack(side="left", padx=(6,12))
        _btn(row,"NOW", self._fill_now,       color=C["txt_dim"]).pack(side="left",padx=(0,6))
        _btn(row,"SET", self._set_exact_time, color=C["accent"]).pack(side="left")
        self._fill_now()

    # ── NTP panel ─────────────────────────────────────────────────────────

    def _build_ntp_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        _lbl(i,"NTP SYNCHRONIZATION", fg=C["txt_dim"], font=("Courier New",8,"bold"),
             bg=C["panel"], anchor="w").pack(fill="x", pady=(0,8))
        row = _frm(i, bg=C["panel"]); row.pack(fill="x", pady=(0,8))
        self._ntp_lbl = _lbl(row,"●  checking...", fg=C["txt_dim"],
                              font=("Courier New",10), bg=C["panel"])
        self._ntp_lbl.pack(side="left")
        _btn(row,"ENABLE NTP",  lambda: self._set_ntp(True),
             color=C["accent3"]).pack(side="right", padx=(6,0))
        _btn(row,"DISABLE NTP", lambda: self._set_ntp(False),
             color=C["err"]).pack(side="right")
        sr = _frm(i, bg=C["panel"]); sr.pack(fill="x", pady=(0,4))
        _btn(sr,"RESTORE CLOCK FROM SNAPSHOT",
             self._restore_clock, color=C["accent"]).pack(side="left")
        self._restore_lbl = _lbl(i,"disable NTP first to save snapshot",
                                  fg=C["txt_dim"], font=("Courier New",8),
                                  bg=C["panel"], anchor="w")
        self._restore_lbl.pack(fill="x")

    # ── Timezone panel ────────────────────────────────────────────────────

    def _build_tz_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        _lbl(i,"TIMEZONE", fg=C["txt_dim"], font=("Courier New",8,"bold"),
             bg=C["panel"], anchor="w").pack(fill="x", pady=(0,8))
        row = _frm(i, bg=C["panel"]); row.pack(fill="x")
        self._tz_combo = ttk.Combobox(row, textvariable=self._tz_var,
                                      font=("Courier New",10), width=28)
        self._tz_combo.pack(side="left", padx=(0,8))
        _btn(row,"APPLY", self._apply_tz, color=C["accent"]).pack(side="left")
        threading.Thread(target=self._load_tz, daemon=True).start()
        try: cur = datetime.datetime.now().astimezone().tzname()
        except: cur = "?"
        _lbl(i, f"current: {cur}", fg=C["txt_dim"],
             font=("Courier New",9), bg=C["panel"], anchor="w").pack(fill="x", pady=(6,0))

    # ── Sparkline chart ───────────────────────────────────────────────────

    def _build_chart_panel(self, p):
        f = _panel(p); f.pack(fill="x", pady=(0,10))
        i = _frm(f, bg=C["panel"]); i.pack(fill="x", padx=16, pady=12)
        _lbl(i,"OFFSET HISTORY (2 min)", fg=C["txt_dim"],
             font=("Courier New",8,"bold"), bg=C["panel"], anchor="w").pack(fill="x", pady=(0,4))
        self._chart = tk.Canvas(i, height=80, bg=C["panel2"], highlightthickness=0)
        self._chart.pack(fill="x")
        lr = _frm(i, bg=C["panel"]); lr.pack(fill="x", pady=(4,0))
        self._chart_min = _lbl(lr,"min: 0ms", fg=C["txt_dim"],
                                font=("Courier New",8), bg=C["panel"])
        self._chart_min.pack(side="left")
        self._chart_max = _lbl(lr,"max: 0ms", fg=C["txt_dim"],
                                font=("Courier New",8), bg=C["panel"])
        self._chart_max.pack(side="right")

    # ── Log ───────────────────────────────────────────────────────────────

    def _build_log_panel(self, p):
        f = _panel(p); f.pack(fill="both", expand=True)
        i = _frm(f, bg=C["panel"]); i.pack(fill="both", expand=True, padx=16, pady=12)
        hdr = _frm(i, bg=C["panel"]); hdr.pack(fill="x", pady=(0,4))
        _lbl(hdr,"OPERATIONS LOG", fg=C["txt_dim"],
             font=("Courier New",8,"bold"), bg=C["panel"]).pack(side="left")
        b_clear = _btn(hdr,"CLEAR", self._clear_log, color=C["txt_dim"])
        b_clear.config(padx=8, pady=2)
        b_clear.pack(side="right")
        fr = _frm(i, bg=C["panel"]); fr.pack(fill="both", expand=True)
        sb = ttk.Scrollbar(fr, orient="vertical"); sb.pack(side="right", fill="y")
        self._log_txt = tk.Text(fr, bg=C["panel2"], fg=C["txt"],
                                font=("Courier New",9), state="disabled",
                                relief="flat", bd=0, wrap="word",
                                yscrollcommand=sb.set, height=8)
        self._log_txt.pack(side="left", fill="both", expand=True)
        sb.config(command=self._log_txt.yview)
        self._log_txt.tag_config("ok",   foreground=C["accent3"])
        self._log_txt.tag_config("err",  foreground=C["err"])
        self._log_txt.tag_config("info", foreground=C["txt_dim"])
        self._log_txt.tag_config("ts",   foreground=C["txt_dim"])

    # ══════════════════════════════════════════════════════════ Actions ══

    def _do_step(self, ms: int):
        """Worker does ONLY the syscall and puts result in queue.
        _tick reads the queue on main thread — _total_ms only ever written there."""
        mono_snap = self._mono_ref
        wall_snap = self._wall_ref

        def _work():
            elapsed = time.monotonic() - mono_snap
            target  = wall_snap + datetime.timedelta(seconds=elapsed, milliseconds=ms)
            ok, msg = set_system_time(target)
            self._step_q.put((ms, ok, msg))

        threading.Thread(target=_work, daemon=True).start()

    def _apply_dt(self):
        try:
            dt_s = float(self._dt_entry.get().strip())
        except ValueError:
            self._log("DT: invalid value", "err"); return
        if abs(dt_s) > 30:
            self._log("DT: value > 30s — check input", "err"); return
        self._do_step(int(-dt_s * 1000))
        self._update_tol_bar(dt_s)

    def _update_tol_bar(self, dt_s: float):
        def _draw():
            c = self._tol_canvas
            try: W=c.winfo_width(); H=c.winfo_height()
            except: return
            if W<4: W=300; H=14
            c.delete("all")
            c.create_rectangle(0,0,W,H, fill=C["panel2"], outline="")
            cx=W//2; c.create_line(cx,0,cx,H, fill=C["txt_dim"])
            zone=int(W*0.5/2)
            c.create_rectangle(cx-zone,2,cx+zone,H-2, fill=C["panel"], outline=C["border"])
            MAX=2.0; ratio=max(-1.0,min(1.0,dt_s/MAX))
            bw=int(abs(ratio)*(W//2))
            x0,x1 = (cx,cx+bw) if ratio>=0 else (cx-bw,cx)
            col=(C["accent3"] if abs(dt_s)<0.5 else C["warn"] if abs(dt_s)<1.0 else C["err"])
            if bw>0: c.create_rectangle(x0,2,x1,H-2, fill=col, outline="")
            st="✓ OK" if abs(dt_s)<0.5 else ("⚠" if abs(dt_s)<1.0 else "✗ OUT")
            self._tol_lbl.config(text=f"DT = {dt_s:+.3f} s  {st}", fg=col)
        self.after(0, _draw)

    def _set_exact_time(self):
        try:
            dt = datetime.datetime.strptime(
                f"{self._date_entry.get().strip()} {self._time_entry.get().strip()}",
                "%Y-%m-%d %H:%M:%S")
        except ValueError:
            messagebox.showerror("Format", "Date: YYYY-MM-DD  Time: HH:MM:SS"); return
        def _work():
            ok, msg = set_system_time(dt)
            if ok:
                # Re-anchor reference to the newly set time
                new_mono = time.monotonic()
                self._step_q.put(("set", dt, new_mono))
                self._log(f"Time set to {dt.strftime('%Y-%m-%d %H:%M:%S')}", "ok")
            else:
                self._log(f"Set time FAILED: {msg}", "err")
        threading.Thread(target=_work, daemon=True).start()

    def _fill_now(self):
        now = datetime.datetime.now()
        self._date_entry.delete(0,"end"); self._date_entry.insert(0,now.strftime("%Y-%m-%d"))
        self._time_entry.delete(0,"end"); self._time_entry.insert(0,now.strftime("%H:%M:%S"))

    def _set_ntp(self, enable: bool):
        def _work():
            if not enable:
                # Snapshot accurate time before disabling NTP
                snap_wall = datetime.datetime.now()
                snap_mono = time.monotonic()
                self._step_q.put(("snap", snap_wall, snap_mono))
            fn = ntp_enable if enable else ntp_disable
            ok, msg = fn()
            self._log(f"NTP {'enabled' if enable else 'disabled'}: {msg}",
                      "ok" if ok else "err")
            self.after(0, self._refresh_ntp_status_label)
        threading.Thread(target=_work, daemon=True).start()

    def _refresh_ntp_status_label(self):
        def _work():
            active = ntp_status()
            col  = C["accent3"] if active else C["err"]
            text = "●  NTP active" if active else "●  NTP inactive"
            self.after(0, lambda: self._ntp_lbl.config(text=text, fg=col))
        threading.Thread(target=_work, daemon=True).start()

    def _restore_clock(self):
        """Restore OS clock to the monotonic-derived correct time. Instant, no blocking."""
        elapsed    = time.monotonic() - self._mono_ref
        correct_dt = self._wall_ref + datetime.timedelta(seconds=elapsed)
        drift_ms   = int((correct_dt - datetime.datetime.now()).total_seconds() * 1000)
        sign = "+" if drift_ms >= 0 else ""
        if abs(drift_ms) < 10:
            self._restore_lbl.config(
                text=f"already accurate (drift {sign}{drift_ms} ms)", fg=C["accent3"])
            self._log(f"RESTORE: already accurate ({sign}{drift_ms} ms)", "ok")
            return
        ok, msg = set_system_time(correct_dt)
        if ok:
            self._restore_lbl.config(text=f"corrected {sign}{drift_ms} ms", fg=C["accent3"])
            self._log(f"RESTORE: corrected {sign}{drift_ms} ms", "ok")
        else:
            self._restore_lbl.config(text=f"failed: {msg}", fg=C["err"])
            self._log(f"RESTORE FAILED: {msg}", "err")

    def _apply_tz(self):
        tz = self._tz_var.get().strip()
        if not tz: return
        def _work():
            ok, msg = set_timezone(tz)
            self._log(f"TZ {'set to '+tz if ok else 'FAILED: '+msg}", "ok" if ok else "err")
        threading.Thread(target=_work, daemon=True).start()

    def _load_tz(self):
        zones = get_timezones()
        self.after(0, lambda: self._tz_combo.config(values=zones))
        try:
            name = str(datetime.datetime.now().astimezone().tzinfo)
            if name in zones:
                self.after(0, lambda: self._tz_var.set(name))
        except: pass

    def _log(self, msg: str, tag: str = "info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        def _ins():
            self._log_txt.config(state="normal")
            self._log_txt.insert("end", f"[{ts}] ","ts")
            self._log_txt.insert("end", msg+"\n", tag)
            self._log_txt.see("end")
            self._log_txt.config(state="disabled")
        self.after(0, _ins)

    def _clear_log(self):
        self._log_txt.config(state="normal")
        self._log_txt.delete("1.0","end")
        self._log_txt.config(state="disabled")

    def _redraw_chart(self):
        c = self._chart
        try: W=c.winfo_width(); H=c.winfo_height()
        except: return
        if W<4 or H<4: return
        c.delete("all")
        vals = self._history.values()
        if not vals: return
        mn,mx=min(vals),max(vals); span=mx-mn if mx!=mn else 1
        for idx in range(1,4):
            y=int(H*idx/4)
            c.create_line(0,y,W,y, fill=C["border"], dash=(2,4))
        zero_y=H-int((0-mn)/span*H) if span else H//2
        c.create_line(0,zero_y,W,zero_y, fill=C["txt_dim"], dash=(4,4))
        n=len(vals); pts=[]
        for idx,v in enumerate(vals):
            x=int(W*idx/max(n-1,1))
            y=H-int((v-mn)/span*(H-4))-2
            pts.extend([x,y])
        if len(pts)>=4:
            c.create_line(*pts, fill=C["accent"], width=2, smooth=True)
            lx,ly=pts[-2],pts[-1]
            c.create_oval(lx-4,ly-4,lx+4,ly+4, fill=C["accent"], outline="")
        self._chart_min.config(text=f"min: {mn:+d}ms")
        self._chart_max.config(text=f"max: {mx:+d}ms")

    # ══════════════════════════════════════════════════════════ Main tick ══

    def _tick(self):
        if not self._running:
            return

        # ── Drain queue (ONLY place _total_ms / references are mutated) ──
        while True:
            try:
                item = self._step_q.get_nowait()
            except queue.Empty:
                break

            kind = item[0]

            if kind == "snap":
                # NTP disable snapshot: re-anchor reference
                _, wall, mono = item
                self._wall_ref = wall
                self._mono_ref = mono
                self._restore_lbl.config(
                    text="snapshot saved — ready to restore", fg=C["accent3"])

            elif kind == "set":
                # Exact time was set: re-anchor to new time
                _, new_wall, new_mono = item
                self._wall_ref = new_wall
                self._mono_ref = new_mono

            else:
                # Normal step: (ms, ok, msg)
                ms, ok, msg = item
                if ok:
                    self._total_ms += ms
                    # Advance the wall reference by the step so display stays sync
                    self._wall_ref = self._wall_ref + datetime.timedelta(milliseconds=ms)
                    # mono_ref stays the same — only wall_ref shifts
                    sign = "+" if ms > 0 else ""
                    self._log(f"Step {sign}{ms} ms  →  total {self._total_ms:+d} ms","ok")
                else:
                    self._log(f"Step FAILED: {msg}","err")

        # ── Clock display ─────────────────────────────────────────────────
        elapsed = time.monotonic() - self._mono_ref
        now = self._wall_ref + datetime.timedelta(seconds=elapsed)
        self._clock_var.set(now.strftime("%H:%M:%S"))
        self._date_var.set(now.strftime("%A, %d %B %Y"))
        try: self._tz_display.set(now.astimezone().tzname())
        except: pass

        # ── Offset + chart ────────────────────────────────────────────────
        sign = "+" if self._total_ms >= 0 else ""
        self._offset_var.set(f"offset  {sign}{self._total_ms} ms")
        self._history.push(self._total_ms)
        self._redraw_chart()

        self.after(500, self._tick)

    # ══════════════════════════════════════════════════════════ Cleanup ══

    def destroy(self):
        self._running = False
        super().destroy()


# ══════════════════════════════════════════════════════════════════ main ══

if __name__ == "__main__":
    app = SysClockApp()

    style = ttk.Style(app)
    style.theme_use("clam")
    style.configure("TCombobox",
                    fieldbackground=C["panel2"], background=C["panel2"],
                    foreground=C["txt"], selectbackground=C["accent"],
                    selectforeground=C["bg"], bordercolor=C["border"],
                    lightcolor=C["panel2"], darkcolor=C["panel2"],
                    arrowcolor=C["accent"])
    style.configure("TScrollbar",
                    background=C["panel2"], troughcolor=C["panel"],
                    bordercolor=C["border"], arrowcolor=C["txt_dim"])

    app._log("System Time Control started", "info")
    app._log(f"OS: {OS}  |  Python {sys.version.split()[0]}", "info")
    if not _is_admin():
        app._log("WARNING: not running as root/admin — system calls may fail", "err")
        tip = "run as Administrator" if OS=="Windows" else "sudo python3 sysclock_gui.py"
        app._log(f"Tip: {tip}", "info")

    app.mainloop()
