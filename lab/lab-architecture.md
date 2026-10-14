# Purple-Team Campaign Lab — Attack Architecture

> **Scope:** single-host incident lab · isolated · confidential (supervisory review)
> **Scenario:** phishing → C2 → persistence → exfiltration. The defender side (Sysmon +
> Windows Defender + Elastic) runs on the victim and requires **no operator action** —
> all evidence is captured automatically.

## Diagram

```
                                    ┌─────────────────────────────┐
                                    │        🌍 INTERNET           │
                                    │  mail provider (phishing)    │
                                    └──────────────┬──────────────┘
                                                   │ ④ phishing email
                                                   │    (NAT egress)
                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                          WINDOWS HOST  (attacker machine, also the C2)                │
│                                                                                       │
│   ┌────────────────────────────────────────────────────────────────────────────────┐  │
│   │  🖥 VICTIM — Windows 11 VM  ("office worker")                                   │  │
│   │     VMware NAT adapter · 192.168.254.128 · gw .2                               │  │
│   │                                                                                │  │
│   │   👤 worker action (ONLY manual step in whole campaign):                        │  │
│   │        opens phishing PDF → clicks "RSVP" link                                 │  │
│   │        → downloads & runs beacon                                               │  │
│   │                                                                                │  │
│   │   🛡 on-host telemetry (defender side — fully passive):                        │  │
│   │        Sysmon (EID 1 proc / 3 net / 11 file)                                   │  │
│   │        Windows Defender · Elastic agent                                        │  │
│   └────────────────────────────────────────────────────────────────────────────────┘  │
│        │ ① GET /office_update.exe (payload fetch, 256 KB)          ┆ telemetry ┆       │
│        │    :80                                                    ┆ stream    ┆       │
│        │ ② beacon reverse-TCP :443                                 ┆           ┆       │
│        ▼                                                           ┆           ┆       │
│   ┌───────────────────────────────────┐                            ┆           ┆       │
│   │  🌐 C2 FRONT-END  (c2_relay.py)   │                            ┆           ┆       │
│   │  bind 192.168.254.100             │                            ┆           ┆       │
│   │     :80  serves payload           │                            ┆           ┆       │
│   │     :443 beacon listener          │                            ┆           ┆       │
│   └──────────────┬────────────────────┘                            ┆           ┆       │
│                  │ ③ TCP relay (shared host loopback)               ┆           ┆       │
│                  │                                                  ▼           ▼       │
│   ┌──────────────┴───────────────────────────────┐    ┌──────────────────────────────┐ │
│   │  🐧 KALI (WSL2, mirrored mode)               │    │  🛡 ELASTIC (defender side)  │ │
│   │                                              │    │                              │ │
│   │  ┌──────────────────────┐ ┌───────────────┐  │    │  • ingest Sysmon EID 1/3/11  │ │
│   │  │ 🎯 msfconsole handler│ │ 📦 http.server│  │    │  • security alerts          │ │
│   │  │ 127.0.0.1:4445       │ │ 127.0.0.1:8090│  │    │  • KQL / hunt               │ │
│   │  │ meterpreter(stageless)│ │ /tmp payload  │  │    │  • = incident-report        │ │
│   │  └──────────────────────┘ └───────────────┘  │    │      evidence store          │ │
│   │            ▲  built by  ▲                       │    └──────────────────────────────┘ │
│   │            │            │                       │                                     │
│   │  ┌──────────────────────────────┐               │                                     │
│   │  │ msfvenom:                     │               │                                     │
│   │  │ windows/x64/meterpreter_      │               │                                     │
│   │  │ reverse_tcp (stageless)       │               │                                     │
│   │  │ 256,000 B  sha256 eb5e9b8d…   │               │                                     │
│   │  └──────────────────────────────┘               │                                     │
│   └──────────────────────────────────────────────────┘                                     │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

## Attack flow (numbered as in the diagram)

| #   | Step                              | Path                          | Detail |
|-----|-----------------------------------|-------------------------------|--------|
| ①   | **Initial access — payload fetch** | VM `:80` → C2 `192.168.254.100` | Worker opens the event-invitation PDF, clicks the "RSVP" link; browser downloads the 256 KB stageless meterpreter beacon |
| ②   | **C2**                            | VM → C2 `:443`                | Beacon reverse-TCPs to the C2 front-end |
| ③   | **Relay → handler**               | C2 `:443` → `127.0.0.1:4445`  | `c2_relay.py` (host) forwards the beacon over the shared mirrored-WSL loopback to the Kali msfconsole handler → **meterpreter session** |
| ④   | **Phish delivery / internet egress** | host → Internet (NAT)     | Phishing email sent to the worker's mailbox; VM reads it with real internet (NAT) |
| —   | **Persistence / privesc / exfil** | live meterpreter session      | Run key + scheduled task + `C:\ProgramData` drop; optional `getsystem`; exfil of `Q3_sales.xlsx` |
| —   | **Telemetry (defender)**          | VM → Elastic (host)           | Sysmon/Defender events flow continuously; this is the incident-report evidence |

## Key addresses

| Component                  | Address |
|----------------------------|---------|
| C2 front-end (host)        | `192.168.254.100` — `:80` payload / `:443` beacon |
| Victim VM                  | `192.168.254.128` (VMware NAT segment `192.168.254.0/24`, gateway `.2`) |
| Kali meterpreter handler   | `127.0.0.1:4445` (host-shared loopback, mirrored WSL) |
| Kali payload HTTP          | `127.0.0.1:8090` (serves `/tmp/office_update.exe`) |
| Beacon                     | `windows/x64/meterpreter_reverse_tcp`, stageless, 256,000 B, SHA256 `eb5e9b8d…4148e2` |

## Design notes

- **One laptop, two segments.** The attacker (Kali in mirrored WSL2) lives on the Wi-Fi
  segment; the victim sits on VMware's NAT segment. The Windows host bridges them and
  *is* the C2 — so the victim's callbacks never cross a segment the host can't see.
- **Stageless payload.** The beacon ships as a single self-contained blob: no second-stage
  download, so nothing to interrupt and no reflective stage load to flag.
- **Defender side is fully passive.** The operator runs the attack only; Sysmon + Elastic
  on the victim record every artifact (cradle, download, beacon, persistence, exfil) for
  the MyCERT-style incident report.
- **Isolation.** Host-only/NAT lab network; the only egress is the intentional NAT path
  used for the phishing email.
