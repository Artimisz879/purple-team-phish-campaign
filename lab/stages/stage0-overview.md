# Kill-Chain Overview

| # | Stage | MITRE | Port | SIEM dataset / event |
|---|---|---|---|---|
| 1 | Phish (PDF + RSVP link) | T1566.001 | 8080 | network (msedge → :8080) |
| 2 | Execute + C2 beacon | T1204.002, T1071.001 | 4443 | endpoint process + network + Elastic Defend alert |
| 3 | Escalate (UAC → migrate) | T1548, T1055 | 4443 | PS 4104 scriptblock + process tree |
| 4 | Persist (task + Run key) | T1053.005, T1547.001 | — | process + **TaskCache/Run registry writes** |
| 5 | Exfil (WebClient upload) | T1041 | 4444 | PS 4104 scriptblock + network egress |

**Infrastructure:** victim `192.168.254.128` · attacker `192.168.254.100`
(8080 serve / 4443 C2 / 4444 data) · Kali WSL2 (msfvenom + msfconsole on `127.0.0.1:4445`)
· Elastic Security 9.x SIEM.

**Timeline (lab run, UTC):** 03:59 first execution → 05:03 beacon C2 → 05:13 UAC elevation →
05:21 SYSTEM (post-migrate) → 05:26–05:30 persistence planted → 05:32 exfil.
